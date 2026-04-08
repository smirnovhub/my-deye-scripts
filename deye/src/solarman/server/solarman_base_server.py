import socket
import threading
import socketserver
import asyncio
import logging
import platform
from typing import Optional

from umodbus.client.serial.redundancy_check import add_crc

from umodbus.functions import (
  ReadHoldingRegisters,
  ReadInputRegisters,
  WriteMultipleRegisters,
  ReadCoils,
  create_function_from_request_pdu,
)

from pysolarmanv5.pysolarmanv5 import CONTROL_CODE, PySolarmanV5, V5FrameError

from mock_data_logger import MockDatalogger

_WIN_PLATFORM = True if platform.system() == "Windows" else False

socketserver.TCPServer.allow_reuse_address = True
socketserver.TCPServer.allow_reuse_port = True # type: ignore

class SolarmanBaseServer():
  """
  Asynchronous TCP server simulating a Solarman Modbus-like device.

  This server handles multiple client connections concurrently using asyncio.
  It maintains internal registers, supports read/write requests, and generates
  appropriate Modbus-like responses. Designed for testing, simulation, or
  as a lightweight mock device for development purposes.

  Features
  --------
  - Maintains register values and tracks read/write operations.
  - Handles standard Modbus function codes: Read Coils, Read Holding Registers,
    Read Input Registers, Write Multiple Registers.
  - Generates valid Modbus CRC frames for responses.
  - Supports asynchronous streaming over TCP.
  - Can run either in the current asyncio event loop or in a dedicated thread.
  """
  def __init__(
    self,
    name: str,
    address: str,
    serial: int,
    port: int = 8899,
  ):
    self._name = name
    self._address = address
    self._serial = serial
    self._port = port

    self._log = logging.getLogger()
    self._log.info(f"{self._name}: starting SolarmanServer at {address}:{port}")

    self._server: Optional[asyncio.AbstractServer] = None

    try:
      self._loop = asyncio.get_running_loop()
      self._loop.create_task(self.start_server())
    except RuntimeError:
      self._loop = asyncio.new_event_loop()
      thr = threading.Thread(target = self.sync_runner, daemon = True)
      thr.start()

  @property
  def name(self) -> str:
    return self._name

  async def start_server(self) -> None:
    """
    Start the asynchronous TCP server

    This method starts an asyncio-based TCP server that listens for
    incoming client connections and handles them using `stream_handler`.

    Notes
    -----
    - Intended for test or simulation environments.
    - Uses reuse_address and reuse_port where supported.
    - For Windows, reuse_port is disabled due to platform limitations.
    """
    self._server = await asyncio.start_server(
      self.stream_handler,
      host = self._address,
      port = self._port,
      family = socket.AF_INET,
      reuse_address = True,
      reuse_port = False if _WIN_PLATFORM else True,
    )

    self._log.info(f"Solarman server {self.name} started at {self._address}:{self._port}")

    async with self._server:
      await self._server.serve_forever()

  async def stop_server_async(self) -> None:
    self._log.info(f"Solarman server {self.name} is stopping...")
    if self._server:
      # Stop accepting new connections
      self._server.close()
      # Wait until the server is fully closed
      await self._server.wait_closed()
      self._server = None
      self._log.info(f"Solarman server {self.name} stopped.")
    else:
      self._log.error(f"Solarman server {self.name} is not running.")

  def stop_server_sync(self) -> None:
    if not self._loop.is_running():
      self._log.error(f"Async loop for Solarman server {self.name} is not running.")
      return

    # Define the shutdown sequence
    async def shutdown():
      await self.stop_server_async()
      # Stop the loop itself
      self._loop.stop()

    # Schedule the shutdown coroutine in the loop
    asyncio.run_coroutine_threadsafe(shutdown(), self._loop)

  def sync_runner(self) -> None:
    """
    Run the asynchronous server in a dedicated thread

    This method schedules `start_server` in the event loop and runs
    the loop forever. Useful when there is no running asyncio loop,
    e.g., when starting the test server from a synchronous context.
    """
    self._loop.create_task(self.start_server())
    self._loop.run_forever()

  async def stream_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Asynchronous handler for an individual TCP client connection.

    This method runs in a loop, reading incoming Modbus-like frames from the client,
    decoding them using a mock Solarman datalogger, generating appropriate responses
    based on register values or simulated data, and sending the responses back.
    The loop exits when the client disconnects or a critical frame error occurs.

    Parameters
    ----------
    reader : asyncio.StreamReader
        Asynchronous stream reader for receiving data from the client.
    writer : asyncio.StreamWriter
        Asynchronous stream writer for sending data to the client.
    """
    sol = MockDatalogger(self._address, serial = self._serial, auto_reconnect = False)
    while True:
      data = await reader.read(1024)
      if data == b"":
        break
      else:
        sol.sequence_number = data[5]
        self._log.debug(f"{self._name}: RECD: {data.hex(' ')}")
        data = bytearray(data)
        data[3] = 0x10
        data[4] = PySolarmanV5._get_response_code(CONTROL_CODE.REQUEST)
        try:
          checksum = sol._calculate_v5_frame_checksum(bytes(data))
        except:
          writer.write(b"")
          await writer.drain()
          break
        data[-2:-1] = checksum.to_bytes(1, byteorder = "big")
        data = bytes(data)
        self._log.debug(f"{self._name}: DEC: {data.hex(' ')}")

        try:
          decoded = sol._v5_frame_decoder(data)
          enc = self.function_response_from_request(decoded)
          self._log.debug(f'{self._name}: Generated Raw modbus: {enc.hex(" ")}')
          enc = sol.v5_frame_response_encoder(enc)
          self._log.debug(f'{self._name}: Sending frame: {bytes(enc).hex(" ")}')
          writer.write(bytes(enc))
          await writer.drain()
        except V5FrameError as e:
          # Close immediately - allows testing with wrong serial numbers, sequence numbers etc.
          self._log.info(f"{self._name}: V5FrameError({' '.join(e.args)}). Closing immediately... ")
          break
        except Exception as e:
          self._log.exception(e)
          writer.write(data)

    try:
      writer.write(b"")
      await writer.drain()
      writer.close()
    except:
      pass

  def function_response_from_request(self, req: bytes) -> bytes:
    """
    Generate a Modbus-like response for a given request (for testing purposes).

    This method decodes the incoming request PDU, processes the requested function
    (Read Coils, Read Holding Registers, Read Input Registers, Write Multiple Registers),
    updates internal register tracking, and returns a response frame with CRC.

    Parameters
    ----------
    req : bytes
        The raw request frame received from the client.

    Returns
    -------
    bytes
        The Modbus-like response frame including CRC.
    """
    res = b""
    func = create_function_from_request_pdu(req[2:-2])

    if isinstance(func, ReadCoils):
      res = self.on_read_coils(func)
    elif isinstance(func, ReadHoldingRegisters):
      res = self.on_read_holding_registers(func)
    elif isinstance(func, ReadInputRegisters):
      res = self.on_read_input_registers(func)
    elif isinstance(func, WriteMultipleRegisters):
      res = self.on_write_multiple_registers(func)

    slave_addr = req[1:2]
    return add_crc(slave_addr + res)

  def on_read_coils(self, func: ReadCoils) -> bytes:
    return b""

  def on_read_holding_registers(self, func: ReadHoldingRegisters) -> bytes:
    return b""

  def on_read_input_registers(self, func: ReadInputRegisters) -> bytes:
    return b""

  def on_write_multiple_registers(self, func: WriteMultipleRegisters) -> bytes:
    return b""
