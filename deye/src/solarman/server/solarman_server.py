import socket
import threading
import socketserver
import asyncio
import random
import logging
import platform

from typing import Dict, List, Set

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

class AioSolarmanServer():
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
    self.name = name
    self.address = address
    self.serial = serial
    self.port = port
    self.log = logging.getLogger()
    self.log.info(f"{self.name}: starting AioSolarmanServer at {address}:{port}")
    self.registers: Dict[int, int] = {}
    self.readed_registers: Set[int] = set()
    self.written_registers: Set[int] = set()

    try:
      self.loop = asyncio.get_running_loop()
      self.loop.create_task(self.start_server())
    except RuntimeError:
      self.loop = asyncio.new_event_loop()
      thr = threading.Thread(target = self.sync_runner, daemon = True)
      thr.start()

  def set_register_value(self, address: int, value: int):
    """
    Set the value of a single register (for testing purposes).

    This method is intended for simulating device registers in a test
    environment. It updates the internal register dictionary and logs the change.

    Parameters
    ----------
    address : int
        The address of the register to set.
    value : int
        The value to store in the register.
    """
    self.log.info(f"{self.name}: setting register value {{{address}: {value}}}")
    self.registers[address] = value

  def set_register_values(self, starting_address: int, values: List[int]):
    """
    Set multiple register values starting from a given address (for testing purposes).

    This method is intended for simulating device registers in a test environment.
    It updates the internal register dictionary and logs all changes.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to set.
    values : List[int]
        The list of values to store in consecutive registers.
    """
    regs_dict = {starting_address + i: val for i, val in enumerate(values)}
    self.log.info(f"{self.name}: setting register values {regs_dict}")
    self.registers.update(regs_dict)

  def clear_registers(self):
    """
    Clear all register values (for testing purposes).

    This method resets the internal register dictionary, effectively
    simulating a device with no stored values.
    """
    self.registers.clear()

  def clear_registers_status(self):
    """
    Clear the read and written registers tracking (for testing purposes).

    This method resets the sets that track which registers have been read
    or written, simulating a fresh device state for testing.
    """
    self.readed_registers.clear()
    self.written_registers.clear()

  def is_registers_readed(self, starting_address: int, quantity: int):
    """
    Check if a range of registers has been read (for testing purposes).

    This method returns True if all registers in the specified range
    have been marked as read in the internal tracking set.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to check.
    quantity : int
        The number of consecutive registers to check.

    Returns
    -------
    bool
        True if all specified registers have been read, False otherwise.
    """
    for address in range(starting_address, starting_address + quantity):
      if address not in self.readed_registers:
        return False
    return True

  def is_registers_written(self, starting_address: int, quantity: int):
    """
    Check if a range of registers has been written (for testing purposes).

    This method returns True if all registers in the specified range
    have been marked as written in the internal tracking set.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to check.
    quantity : int
        The number of consecutive registers to check.

    Returns
    -------
    bool
        True if all specified registers have been written, False otherwise.
    """
    for address in range(starting_address, starting_address + quantity):
      if address not in self.written_registers:
        return False
    return True

  async def start_server(self):
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
    await asyncio.start_server(
      self.stream_handler,
      host = self.address,
      port = self.port,
      family = socket.AF_INET,
      reuse_address = True,
      reuse_port = False if _WIN_PLATFORM else True,
    )

  def sync_runner(self):
    """
    Run the asynchronous server in a dedicated thread

    This method schedules `start_server` in the event loop and runs
    the loop forever. Useful when there is no running asyncio loop,
    e.g., when starting the test server from a synchronous context.
    """
    self.loop.create_task(self.start_server())
    self.loop.run_forever()

  async def stream_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
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
    sol = MockDatalogger(self.address, serial = self.serial, auto_reconnect = False)
    while True:
      data = await reader.read(1024)
      if data == b"":
        break
      else:
        sol.sequence_number = data[5]
        self.log.debug(f"{self.name}: RECD: {data.hex(' ')}")
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
        self.log.debug(f"{self.name}: DEC: {data.hex(' ')}")

        try:
          decoded = sol._v5_frame_decoder(data)
          enc = self.function_response_from_request(decoded)
          self.log.debug(f'{self.name}: Generated Raw modbus: {enc.hex(" ")}')
          enc = sol.v5_frame_response_encoder(enc)
          self.log.debug(f'{self.name}: Sending frame: {bytes(enc).hex(" ")}')
          writer.write(bytes(enc))
          await writer.drain()
        except V5FrameError as e:
          # Close immediately - allows testing with wrong serial numbers, sequence numbers etc.
          self.log.info(f"{self.name}: V5FrameError({' '.join(e.args)}). Closing immediately... ")
          break
        except Exception as e:
          self.log.exception(e)
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
    func = create_function_from_request_pdu(req[2:-2])
    slave_addr = req[1:2]
    res = b""
    if isinstance(func, ReadCoils):
      if func.quantity is None:
        raise ValueError("ReadCoils request missing quantity")
      res = func.create_response_pdu([random.randint(0, 255) for x in range(func.quantity)])
    elif isinstance(func, ReadHoldingRegisters):
      if func.quantity is None or func.starting_address is None:
        raise ValueError("ReadHoldingRegisters request missing starting_address or quantity")
      read_values = self.get_existing_registers_values(func.starting_address, func.quantity)
      res = func.create_response_pdu(read_values)
      new_values = self.get_new_registers_values(func.starting_address, read_values)

      for address in new_values.keys():
        self.readed_registers.add(address)

      self.log.info(f'{self.name}: read registers {new_values}')
    elif isinstance(func, ReadInputRegisters):
      if func.quantity is None:
        raise ValueError("ReadInputRegisters request missing quantity")
      res = func.create_response_pdu([random.randint(0, 2**16 - 1) for x in range(func.quantity)])
    elif isinstance(func, WriteMultipleRegisters):
      if func.starting_address is None or func.values is None:
        raise ValueError("ReadHoldingRegisters request missing starting_address or values")
      write_values = self.get_new_registers_values(func.starting_address, func.values)
      self.registers.update(write_values)

      for address in write_values.keys():
        self.written_registers.add(address)

      res = func.create_response_pdu()
      self.log.info(f'{self.name}: write registers {write_values}')
    return add_crc(slave_addr + res)

  def get_new_registers_values(self, starting_address: int, values: List[int]) -> Dict[int, int]:
    """
    Map a list of values to consecutive register addresses (for testing purposes).

    This method creates a dictionary that assigns each value to a register
    address starting from `starting_address`. Useful for simulating writes
    to multiple registers in a test environment.

    Parameters
    ----------
    starting_address : int
        The starting address for the registers.
    values : List[int]
        The list of values to assign to consecutive registers.

    Returns
    -------
    Dict[int, int]
        A dictionary mapping register addresses to their corresponding values.
    """
    registers: Dict[int, int] = {}
    start = starting_address
    for offset, value in enumerate(values):
      registers[start + offset] = value
    return registers

  def get_existing_registers_values(self, starting_address: int, quantity: int) -> List[int]:
    """
    Retrieve values of consecutive registers (for testing purposes).

    This method returns a list of register values starting from `starting_address`.
    If a register has not been set, its value defaults to 0. Useful for simulating
    reads from a device in a test environment.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to read.
    quantity : int
        The number of consecutive registers to retrieve.

    Returns
    -------
    List[int]
        A list of register values corresponding to the requested addresses.
    """
    return [self.registers.get(i, 0) for i in range(
      starting_address,
      starting_address + quantity,
    )]
