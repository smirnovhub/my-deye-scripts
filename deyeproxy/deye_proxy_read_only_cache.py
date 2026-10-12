import sys
import asyncio
import logging
import signal

from datetime import timedelta

from umodbus.functions import (
  ReadHoldingRegisters,
  ReadInputRegisters,
  WriteMultipleRegisters,
)

from log_utils import LogUtils
from common_utils import CommonUtils
from async_ticker import AsyncTicker
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
      name = self.__class__.__name__,
      address = config.PROXY_HOST,
      port = config.PROXY_PORT,
      serial = config.LOGGER_FAKE_SERIAL,
      logger = self._logger,
    )

    self._config = config

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

  async def _run_ticker(self, ticker: AsyncTicker, stop_event: asyncio.Event) -> None:
    """Wrapper to run the AsyncTicker and handle CancelledError"""
    try:
      async for _ in ticker:
        self._logger.info("Running cache update tasks...")

        # Handle exceptions independently to prevent skipping updates
        try:
          await self._holding_cache.update_cache()
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._logger.error(f"Error updating holding registers cache: {e}")

        # Exit loop immediately if shutdown was requested
        if stop_event.is_set():
          break

        try:
          await self._input_cache.update_cache()
        except asyncio.CancelledError:
          raise
        except Exception as e:
          self._logger.error(f"Error updating input registers cache: {e}")
    except asyncio.CancelledError:
      self._logger.info("Ticker task received CancelledError")
      raise
    finally:
      self._logger.info("Ticker task finished")

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

  async def run(self) -> None:
    ticker = AsyncTicker(
      period = timedelta(seconds = self._config.CACHE_UPDATE_INTERVAL),
      align_with_period = True,
    )

    # Stop event flag
    stop_event = asyncio.Event()

    ticker_task = asyncio.create_task(self._run_ticker(ticker, stop_event))

    def signal_handler(sig_num, frame):
      self._logger.info(f"Signal {sig_num} received, shutting down...")
      stop_event.set()
      ticker.stop()

    # Register signals for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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

    try:
      # Main loop is waiting for stop event
      await stop_event.wait()
    finally:
      self._logger.info("Shutting down caching proxy server...")
      ticker_task.cancel()
      await asyncio.gather(ticker_task, return_exceptions = True)

    await self.stop_server_async()

    self._logger.info("Server stopped.")

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()
