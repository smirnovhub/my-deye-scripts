import struct
import socket
import threading
import socketserver
import asyncio
import random
import logging
import platform

from umodbus.client.serial.redundancy_check import add_crc

from umodbus.functions import (
  ReadHoldingRegisters,
  ReadInputRegisters,
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
  Async version of the test server
  """
  def __init__(self, address: str, serial: int, port = 8899):
    self.address = address
    self.serial = serial
    self.port = port
    self.log = logging.getLogger()
    self.expected_register_address = 0
    self.expected_register_value = 0
    self.log.info(f"Starting AioSolarmanServer at {address} {port}")

    try:
      self.loop = asyncio.get_running_loop()
      self.loop.create_task(self.start_server())
    except RuntimeError:
      self.loop = asyncio.new_event_loop()
      thr = threading.Thread(target = self.sync_runner, daemon = True)
      thr.start()

  async def start_server(self):
    await asyncio.start_server(
      self.stream_handler,
      host = self.address,
      port = self.port,
      family = socket.AF_INET,
      reuse_address = True,
      reuse_port = False if _WIN_PLATFORM else True,
    )

  def set_expected_register_address(self, address: int):
    self.log.info(f"Setting expected register address to {address}")
    self.expected_register_address = address

  def set_expected_register_value(self, value: int):
    self.log.info(f"Setting expected register value to {value}")
    self.expected_register_value = value

  def sync_runner(self):
    self.loop.create_task(self.start_server())
    self.loop.run_forever()

  async def stream_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Stream handler for the async test server

    :param reader:
    :param writer:
    :return:
    """
    sol = MockDatalogger("0.0.0.0", serial = self.serial, auto_reconnect = False)
    count_packet = bytes.fromhex("a5010010478d69b5b50aa2006415")
    non_v5_packet = bytes.fromhex("41542b595a434d505645523d4d57335f3136555f353430365f322e32370d0a0d0a")
    gibberish = bytes.fromhex("aa030a00000000000000000000be9c")
    more_gibberish = bytes.fromhex("0103080100020232333038c75c")
    cl_packets = 0

    while True:
      data = await reader.read(1024)
      cl_packets += 1
      if data == b"":
        break
      else:
        seq_no = data[5]
        sol.sequence_number = data[5]
        self.log.debug(f"[AioHandler] RECD: {data.hex(' ')}")
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
        self.log.debug(f"[AioHandler] DEC: {data.hex(' ')}")
        if cl_packets == 4:
          self.log.debug("C == 4. Writing empty bytes... Expecting reconnect")
          writer.write(b"")
          try:
            await writer.drain()
            break
          except:
            self.log.error("Connection closed......")
            break
        try:
          decoded = sol._v5_frame_decoder(data)
          enc = self.function_response_from_request(decoded)
          self.log.debug(f'[AioHandler] Generated Raw modbus: {enc.hex(" ")}')
          enc = sol.v5_frame_response_encoder(enc)
          self.log.debug(f'[AioHandler] Sending frame: {bytes(enc).hex(" ")}')
          writer.write(bytes(enc))
          await writer.drain()
        except V5FrameError as e:
          """Close immediately - allows testing with wrong serial numbers, sequence numbers etc."""
          self.log.debug(f"[AioHandler] V5FrameError({' '.join(e.args)}). Closing immediately... ")
          break
        except Exception as e:
          self.log.exception(e)
          writer.write(data)
        if cl_packets == 3:
          # Write counter packet and wait some time to be consumed
          await self.random_delay()
          writer.write(count_packet)
          await writer.drain()
          await self.random_delay()
          writer.write(gibberish)
          await writer.drain()
          await self.random_delay()
          writer.write(non_v5_packet)
          await writer.drain()
          await self.random_delay()
          writer.write(more_gibberish)
          await writer.drain()
          await self.random_delay()
    try:
      writer.write(b"")
      await writer.drain()
      writer.close()
    except:
      pass

  def function_response_from_request(self, req: bytes):
    func = create_function_from_request_pdu(req[2:-2])
    if func.starting_address > 4000:
      ex_code = random.choice([1, 2, 3, 4, 5, 6])
      return struct.pack("<H", ex_code)

    slave_addr = req[1:2]
    res = b""
    if isinstance(func, ReadCoils):
      if func.quantity is None:
        raise ValueError("ReadCoils request missing quantity")
      res = func.create_response_pdu([random.randint(0, 255) for x in range(func.quantity)])
    elif isinstance(func, ReadHoldingRegisters):
      if func.quantity is None:
        raise ValueError("ReadHoldingRegisters request missing quantity")
      if self.expected_register_address == func.starting_address:
        res = func.create_response_pdu([self.expected_register_value for x in range(func.quantity)])
      else:
        res = func.create_response_pdu([random.randint(0, 2**16 - 1) for x in range(func.quantity)])
    elif isinstance(func, ReadInputRegisters):
      if func.quantity is None:
        raise ValueError("ReadInputRegisters request missing quantity")
      res = func.create_response_pdu([random.randint(0, 2**16 - 1) for x in range(func.quantity)])
    # Randomly inject Double CRC errors (see GH Issue #62)
    if random.choice([True, False]):
      return add_crc(add_crc(slave_addr + res))
    else:
      return add_crc(slave_addr + res)

  async def random_delay(self):
    await asyncio.sleep(random.randint(10, 50) / 100)
