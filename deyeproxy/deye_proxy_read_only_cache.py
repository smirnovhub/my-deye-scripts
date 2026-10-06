import sys
import asyncio
import logging
import signal

from umodbus.functions import (
  ReadHoldingRegisters,
  ReadInputRegisters,
  WriteMultipleRegisters,
)

from log_utils import LogUtils
from common_utils import CommonUtils
from solarman_base_server import SolarmanBaseServer
from src.deye_proxy_config import DeyeProxyConfig
from src.deye_registers_cache import DeyeRegistersCache
from src.deye_register_type_enum import DeyeRegisterType

config = DeyeProxyConfig()

logger = LogUtils.setup_hourly_overwrite_file_logger(
  name = "deye-proxy-read-only",
  log_dir = f"data/{config.LOG_NAME}",
  log_file_template = "deye-proxy-{0}.log",
)

config.validate_or_exit()

log_level = logging.INFO
if config.LOG_LEVEL in logging._nameToLevel:
  log_level = logging._nameToLevel[config.LOG_LEVEL]

logger.setLevel(log_level)

class CachingSolarmanProxy(SolarmanBaseServer):
  def __init__(self):
    super().__init__(
      name = "CachingProxy",
      address = config.PROXY_HOST,
      port = config.PROXY_PORT,
      serial = config.LOGGER_FAKE_SERIAL,
      logger = logger,
    )

    self._shutdown_event = asyncio.Event()
    self._updater_task = None

    # Dedicated lock to serialize all network operations with remote Solarman client
    logger_client_lock = asyncio.Lock()

    # Caches for Holding and Input registers
    self._holding_cache = DeyeRegistersCache(
      type = DeyeRegisterType.Holding,
      logger_client_lock = logger_client_lock,
      config = config,
      logger = self._log,
    )

    self._input_cache = DeyeRegistersCache(
      type = DeyeRegisterType.Input,
      logger_client_lock = logger_client_lock,
      config = config,
      logger = self._log,
    )

  async def stop_server_async(self) -> None:
    if self._updater_task:
      self._updater_task.cancel()
    await super().stop_server_async()

  async def _background_updater(self):
    while not self._shutdown_event.is_set():
      try:
        # Wait for update interval or wake up immediately on shutdown event
        try:
          await asyncio.wait_for(self._shutdown_event.wait(), timeout = config.CACHE_UPDATE_INTERVAL)
        except asyncio.TimeoutError:
          pass

        # Exit loop immediately if shutdown was requested
        if self._shutdown_event.is_set():
          break

        # Handle exceptions independently to prevent skipping updates
        try:
          await self._holding_cache.update_cache()
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._log.error(f"Error updating holding registers cache: {e}")

        try:
          await self._input_cache.update_cache()
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._log.error(f"Error updating input registers cache: {e}")

      except asyncio.CancelledError:
        break
      except Exception as e:
        self._log.error(f"Error in background updater loop: {e}")

  async def on_read_holding_registers(
    self,
    func: ReadHoldingRegisters,
    client_ip: str,
    client_port: int,
  ) -> bytes:
    if func.starting_address is None or func.quantity is None:
      raise ValueError("ReadHoldingRegisters request missing starting_address or quantity")

    values = await self._holding_cache.get_or_fetch_registers(
      start_address = func.starting_address,
      quantity = func.quantity,
      client_ip = client_ip,
      client_port = client_port,
    )

    return func.create_response_pdu(values)

  async def on_read_input_registers(
    self,
    func: ReadInputRegisters,
    client_ip: str,
    client_port: int,
  ) -> bytes:
    if func.starting_address is None or func.quantity is None:
      raise ValueError("ReadInputRegisters request missing starting_address or quantity")

    values = await self._input_cache.get_or_fetch_registers(
      start_address = func.starting_address,
      quantity = func.quantity,
      client_ip = client_ip,
      client_port = client_port,
    )

    return func.create_response_pdu(values)

  async def on_write_multiple_registers(
    self,
    func: WriteMultipleRegisters,
    client_ip: str,
    client_port: int,
  ) -> bytes:
    if func.starting_address is None or func.values is None:
      raise ValueError("WriteMultipleRegisters request missing starting_address or values")

    self._log.warning(f"{client_ip}:{client_port} Trying to write registers starting at "
                      f"{func.starting_address} with values {func.values}, but this proxy is read-only")

    return func.create_response_pdu()

  def handle_exit(self, sig_num: int) -> None:
    logger.info(f"Received signal {sig_num}. Shutting down gracefully...")
    self._shutdown_event.set()

  async def run(self) -> None:
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
      try:
        loop.add_signal_handler(sig, self.handle_exit, sig)
      except NotImplementedError:
        signal.signal(sig, lambda s, f: self.handle_exit(s))

    external_ip = CommonUtils.get_external_ip(config.LOGGER_HOST, config.LOGGER_PORT)
    actual_ip = external_ip if external_ip else config.PROXY_HOST

    log_level_name = logging._levelToName[log_level]

    logger.info("------- Deye Read-Only Caching Proxy Server started -------")
    logger.info(f"Target logger         : {config.LOGGER_HOST}:{config.LOGGER_PORT}")
    logger.info(f"Logger real serial    : {config.LOGGER_SERIAL}")
    logger.info(f"Logger fake serial    : {config.LOGGER_FAKE_SERIAL}")
    logger.info(f"Listening on          : {actual_ip}:{config.PROXY_PORT}")
    logger.info(f"Cache update interval : {config.CACHE_UPDATE_INTERVAL}s")
    logger.info(f"Cache purge timeout   : {config.CACHE_PURGE_TIMEOUT}s")
    logger.info(f"Read only             : {config.READ_ONLY}")
    logger.info(f"Log level             : {log_level_name}")
    logger.info("-----------------------------------------------------------")

    self._updater_task = asyncio.create_task(self._background_updater())

    await self._shutdown_event.wait()

    logger.info("Shutting down caching proxy server...")

    if self._updater_task:
      self._updater_task.cancel()
      try:
        await self._updater_task
      except asyncio.CancelledError:
        pass

    await super().stop_server_async()

    logger.info("Server stopped.")

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()

async def main_read_only_cache() -> None:
  proxy = CachingSolarmanProxy()
  await proxy.run()
