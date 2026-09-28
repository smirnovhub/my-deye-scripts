"""
Deye Async TCP Proxy Server with Write Command Filtering

Author: Dmitry Smirnov
https://github.com/smirnovhub

This module provides an asynchronous, exclusive-access proxy for communicating with
Solarman V5 data loggers (found in Deye, Sunsynk, and other inverters).

The proxy solves the single-connection limitation of the hardware by queuing
multiple client requests and ensuring only one session is active at a time
using an asynchronous lock. In addition, it filters incoming frames to block
write operations and allow only read Modbus function codes.
"""
import sys
import time
import errno
import logging
import signal
import asyncio

from log_utils import LogUtils
from common_utils import CommonUtils
from src.deye_proxy_config import DeyeProxyConfig

config = DeyeProxyConfig()

logger = LogUtils.setup_hourly_overwrite_file_logger(
  name = "deye-proxy-main",
  log_dir = f"data/{config.LOG_NAME}",
  log_file_template = "deye-proxy-{0}.log",
)

logger_wait = LogUtils.setup_hourly_overwrite_file_logger(
  name = "deye-proxy-wait",
  log_dir = f"data/{config.LOG_NAME}",
  log_file_template = "deye-proxy-wait-{0}.log",
  clear_handlers = False,
)

config.validate_or_exit()

# Allowed Modbus read function codes (Read Coils, Read Discrete Inputs, Read Holding, Read Input)
ALLOWED_READ_FUNCTIONS = {0x01, 0x02, 0x03, 0x04}

log_level = logging.INFO
if config.LOG_LEVEL in logging._nameToLevel:
  log_level = logging._nameToLevel[config.LOG_LEVEL]

class DeyeProxyServer:
  def __init__(self):
    # Asynchronous lock to synchronize access to the physical logger
    self.logger_lock = asyncio.Lock()

    # Asynchronous stop event for managing program lifecycle
    self.shutdown_event = asyncio.Event()

  def is_read_frame(self, frame: bytes) -> bool:
    """Validates frame length, start and end markers, and Modbus function code."""
    if len(frame) < 32 or frame[0] != 0xA5 or frame[-1] != 0x15:
      return False

    func_code = frame[27]
    return func_code in ALLOWED_READ_FUNCTIONS

  async def pipe_client_to_logger(
    self,
    client_reader: asyncio.StreamReader,
    logger_writer: asyncio.StreamWriter,
    client_prefix: str,
  ) -> None:
    """Buffers incoming TCP stream into V5 frames and forwards only read operations."""
    total_bytes = 0
    buffer = bytearray()

    while not self.shutdown_event.is_set():
      try:
        chunk = await asyncio.wait_for(
          client_reader.read(1024),
          timeout = config.CLIENT_IDLE_TIMEOUT,
        )
      except asyncio.TimeoutError:
        logger.error(f"{client_prefix} Client -> Logger timed out after {config.CLIENT_IDLE_TIMEOUT}s of inactivity")
        break
      except (ConnectionResetError, BrokenPipeError):
        logger.error(f"{client_prefix} Client -> Logger connection reset by peer")
        break
      except Exception as e:
        logger.debug(f"{client_prefix} Client -> Logger read exception: {e}")
        break

      if not chunk:
        break

      buffer.extend(chunk)

      while len(buffer) >= 15:
        if buffer[0] != 0xA5:
          pos = buffer.find(b"\xa5")
          if pos == -1:
            buffer.clear()
            break
          del buffer[:pos]

        if len(buffer) < 15:
          break

        payload_len = int.from_bytes(buffer[1:3], byteorder = "little")
        frame_len = payload_len + 13

        if len(buffer) < frame_len:
          break

        frame = bytes(buffer[:frame_len])
        del buffer[:frame_len]

        if not self.is_read_frame(frame):
          logger.warning(f"{client_prefix} Blocked non-read or write command frame!")
          return

        logger_writer.write(frame)
        await logger_writer.drain()
        total_bytes += len(frame)

    logger.info(f"{client_prefix} Client -> Logger bytes sent: {total_bytes}")

  async def pipe_logger_to_client(
    self,
    logger_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
    client_prefix: str,
  ) -> None:
    """Forwards responses from logger back to client without modification."""
    total_bytes = 0

    while not self.shutdown_event.is_set():
      try:
        data = await asyncio.wait_for(
          logger_reader.read(1024),
          timeout = config.LOGGER_IDLE_TIMEOUT,
        )
      except asyncio.TimeoutError:
        logger.error(f"{client_prefix} Logger -> Client timed out after {config.LOGGER_IDLE_TIMEOUT}s of inactivity")
        break
      except (ConnectionResetError, BrokenPipeError):
        logger.error(f"{client_prefix} Logger -> Client connection reset by peer")
        break
      except Exception as e:
        logger.debug(f"{client_prefix} Logger -> Client read exception: {e}")
        break

      if not data:
        break

      client_writer.write(data)
      await client_writer.drain()
      total_bytes += len(data)

    logger.info(f"{client_prefix} Logger -> Client bytes sent: {total_bytes}")

  async def handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter) -> None:
    """Manages a single client session with exclusive logger locking and frame filtering."""
    if self.shutdown_event.is_set():
      client_writer.close()
      await client_writer.wait_closed()
      return

    client_peer = client_writer.get_extra_info("peername")
    client_ip = client_peer[0] if client_peer else "unknown"
    client_port = client_peer[1] if client_peer else 0
    client_prefix = f"{client_ip}:{client_port}"

    start_wait = time.time()
    logger.info(f"{client_prefix} Client wants connect to {config.LOGGER_HOST}:{config.LOGGER_PORT}...")

    try:
      await asyncio.wait_for(self.logger_lock.acquire(), timeout = config.CLIENT_WAIT_TIMEOUT)
    except asyncio.TimeoutError:
      logger.error(f"{client_prefix} Could not acquire lock within "
                   f"{config.CLIENT_WAIT_TIMEOUT}s. Connection rejected.")
      client_writer.close()
      await client_writer.wait_closed()
      return

    session_start = time.time()
    wait_duration = session_start - start_wait

    try:
      if self.shutdown_event.is_set():
        client_writer.close()
        await client_writer.wait_closed()
        return

      logger.info(f"{client_prefix} Lock acquired (waited {wait_duration:.2f}s). Connecting to logger...")

      if wait_duration > 0.1:
        logger_wait.warning(f"{client_prefix} Wait duration: {wait_duration:.2f}s")

      try:
        logger_reader, logger_writer = await asyncio.wait_for(
          asyncio.open_connection(config.LOGGER_HOST, config.LOGGER_PORT),
          timeout = config.CONNECT_TIMEOUT,
        )
      except asyncio.TimeoutError:
        logger.error(f"{client_prefix} Connection to logger timed out")
        return
      except ConnectionRefusedError:
        logger.error(f"{client_prefix} Logger refused connection")
        return
      except OSError as e:
        if e.errno == errno.EHOSTUNREACH:
          logger.error(f"{client_prefix} No route to host")
        else:
          logger.error(f"{client_prefix} Unexpected error: {type(e).__name__}: {e}")
        return

      logger_peer = logger_writer.get_extra_info("peername")
      logger_ip = logger_peer[0] if logger_peer else config.LOGGER_HOST
      logger_port = logger_peer[1] if logger_peer else config.LOGGER_PORT

      logger.info(f"{client_prefix} Bridge established: {client_prefix} <-> {logger_ip}:{logger_port}")

      task_c2l = asyncio.create_task(self.pipe_client_to_logger(client_reader, logger_writer, client_prefix))
      task_l2c = asyncio.create_task(self.pipe_logger_to_client(logger_reader, client_writer, client_prefix))

      try:
        done, pending = await asyncio.wait_for(
          asyncio.wait([task_c2l, task_l2c], return_when = asyncio.FIRST_COMPLETED),
          timeout = config.SESSION_TIMEOUT,
        )
        for task in pending:
          task.cancel()
      except asyncio.TimeoutError:
        logger.error(f"{client_prefix} Session timed out after {config.SESSION_TIMEOUT}s")
        task_c2l.cancel()
        task_l2c.cancel()

    except Exception as ee:
      logger.error(f"{client_prefix} Unexpected error: {type(ee).__name__}: {ee}")
    finally:
      if 'logger_writer' in locals() and not logger_writer.is_closing():
        logger_writer.close()
        try:
          await logger_writer.wait_closed()
        except Exception:
          pass

      if not client_writer.is_closing():
        client_writer.close()
        try:
          await client_writer.wait_closed()
        except Exception:
          pass

      await asyncio.sleep(0.015)

      session_duration = time.time() - session_start + wait_duration
      logger.info(f"{client_prefix} Session finished (duration {session_duration:.2f}s). Lock released")
      logger.info('-----------------------------------------------------------------------')
      self.logger_lock.release()

  def handle_exit(self, sig_num: int) -> None:
    """Signal handler to trigger graceful shutdown."""
    logger.info(f"Received signal {sig_num}. Shutting down gracefully...")
    self.shutdown_event.set()

  async def run(self) -> None:
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
      try:
        loop.add_signal_handler(sig, lambda s = sig: self.handle_exit(s))
      except NotImplementedError:
        signal.signal(sig, lambda s, f: self.handle_exit(s))

    external_ip = CommonUtils.get_external_ip(config.LOGGER_HOST, config.LOGGER_PORT)
    actual_ip = external_ip if external_ip else config.PROXY_HOST

    log_level_name = logging._levelToName[log_level]

    logger.info("------- Deye Read-Only Proxy started -------")
    logger.info(f"Target logger       : {config.LOGGER_HOST}:{config.LOGGER_PORT}")
    logger.info(f"Listening on        : {actual_ip}:{config.PROXY_PORT}")
    logger.info(f"Max connections     : {config.MAX_CONCURRENT_CONNECTIONS}")
    logger.info(f"Client wait timeout : {config.CLIENT_WAIT_TIMEOUT}")
    logger.info(f"Connect timeout     : {config.CONNECT_TIMEOUT}s")
    logger.info(f"Client idle timeout : {config.CLIENT_IDLE_TIMEOUT}s")
    logger.info(f"Logger idle timeout : {config.LOGGER_IDLE_TIMEOUT}s")
    logger.info(f"Session timeout     : {config.SESSION_TIMEOUT}s")
    logger.info(f"Read only           : {config.READ_ONLY}")
    logger.info(f"Log level           : {log_level_name}")
    logger.info("----------------------------------")

    server = await asyncio.start_server(
      self.handle_client,
      config.PROXY_HOST,
      config.PROXY_PORT,
      reuse_address = True,
    )

    async with server:
      server_task = asyncio.create_task(server.serve_forever())
      await self.shutdown_event.wait()
      logger.info("Shutting down proxy server...")
      server.close()
      await server.wait_closed()
      server_task.cancel()

    logger.info("Server socket closed.")

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()

async def main_read_only() -> None:
  proxy = DeyeProxyServer()
  await proxy.run()
