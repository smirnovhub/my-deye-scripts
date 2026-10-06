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

class SolarmanReadOnlyProxy(SolarmanBaseServer):
  def __init__(
    self,
    config: DeyeProxyConfig,
  ):
    self._logger = LogUtils.setup_hourly_overwrite_file_logger(
      name = "deye-proxy-read-only",
      log_dir = f"data/{config.LOG_NAME}",
      log_file_template = "deye-proxy-ro-{0}.log",
    )

    self._log_level = logging.INFO
    if config.LOG_LEVEL in logging._nameToLevel:
      self._log_level = logging._nameToLevel[config.LOG_LEVEL]

    self._logger.setLevel(self._log_level)

    super().__init__(
      name = "CachingProxy",
      address = config.PROXY_HOST,
      port = config.PROXY_PORT,
      serial = config.LOGGER_FAKE_SERIAL,
      logger = self._logger,
    )

    self._config = config
    self._shutdown_event = asyncio.Event()
    self._updater_task = None

    # Dedicated lock to serialize all network operations with remote Solarman client
    logger_client_lock = asyncio.Lock()

    # Caches for Holding and Input registers
    self._holding_cache = DeyeRegistersCache(
      type = DeyeRegisterType.Holding,
      logger_client_lock = logger_client_lock,
      config = config,
      logger = self._logger,
    )

    self._input_cache = DeyeRegistersCache(
      type = DeyeRegisterType.Input,
      logger_client_lock = logger_client_lock,
      config = config,
      logger = self._logger,
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
          await asyncio.wait_for(self._shutdown_event.wait(), timeout = self._config.CACHE_UPDATE_INTERVAL)
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
          self._logger.error(f"Error updating holding registers cache: {e}")

        try:
          await self._input_cache.update_cache()
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._logger.error(f"Error updating input registers cache: {e}")

      except asyncio.CancelledError:
        break
      except Exception as e:
        self._logger.error(f"Error in background updater loop: {e}")

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

    self._logger.warning(f"{client_ip}:{client_port} Trying to write registers starting at "
                         f"{func.starting_address} with values {func.values}, but this proxy is read-only")

    return func.create_response_pdu()

  def _handle_exit(self, sig_num: int) -> None:
    self._logger.info(f"Received signal {sig_num}. Shutting down gracefully...")
    self._shutdown_event.set()

  async def run(self) -> None:
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
      try:
        loop.add_signal_handler(sig, self._handle_exit, sig)
      except NotImplementedError:
        signal.signal(sig, lambda s, f: self._handle_exit(s))

    external_ip = CommonUtils.get_external_ip(self._config.LOGGER_HOST, self._config.LOGGER_PORT)
    actual_ip = external_ip if external_ip else self._config.PROXY_HOST

    log_level_name = logging._levelToName[self._log_level]

    self._logger.info("------- Deye Read-Only Caching Proxy Server started -------")
    self._logger.info(f"Target logger         : {self._config.LOGGER_HOST}:{self._config.LOGGER_PORT}")
    self._logger.info(f"Logger real serial    : {self._config.LOGGER_SERIAL}")
    self._logger.info(f"Logger fake serial    : {self._config.LOGGER_FAKE_SERIAL}")
    self._logger.info(f"Listening on          : {actual_ip}:{self._config.PROXY_PORT}")
    self._logger.info(f"Cache update interval : {self._config.CACHE_UPDATE_INTERVAL}s")
    self._logger.info(f"Cache purge timeout   : {self._config.CACHE_PURGE_TIMEOUT}s")
    self._logger.info(f"Read only             : {self._config.READ_ONLY}")
    self._logger.info(f"Log level             : {log_level_name}")
    self._logger.info("-----------------------------------------------------------")

    self._updater_task = asyncio.create_task(self._background_updater())

    await self._shutdown_event.wait()

    self._logger.info("Shutting down caching proxy server...")

    if self._updater_task:
      self._updater_task.cancel()
      try:
        await self._updater_task
      except asyncio.CancelledError:
        pass

    await super().stop_server_async()

    self._logger.info("Server stopped.")

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()
