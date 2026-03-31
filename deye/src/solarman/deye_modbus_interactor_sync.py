from typing import Dict
from datetime import datetime

from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_modbus_interactor import DeyeModbusInteractor
from deye_modbus_solarman import DeyeModbusSolarman
from deye_register_cache_data import DeyeRegisterCacheData
from deye_registers_base_cache_manager import DeyeRegistersBaseCacheManager
from deye_registers_local_cache_manager import DeyeRegistersLocalCacheManager
from deye_registers_remote_cache_manager import DeyeRegistersRemoteCacheManager

class DeyeModbusInteractorSync(DeyeModbusInteractor):
  def __init__(
    self,
    logger: DeyeLogger,
    **kwargs,
  ):
    super().__init__(
      logger = logger,
      **kwargs,
    )

    self._solarman = DeyeModbusSolarman(logger, **kwargs)

    # Initialize cache manager
    self._cache_manager: DeyeRegistersBaseCacheManager
    if self._loggers.remote_cache_server:
      self._cache_manager = DeyeRegistersRemoteCacheManager(
        name = self._logger.name,
        serial = self._logger.serial,
        remote_cache_server = self._loggers.remote_cache_server,
      )
    else:
      self._cache_manager = DeyeRegistersLocalCacheManager(
        name = self._logger.name,
        serial = self._logger.serial,
      )

  def process_enqueued_registers(self) -> None:
    if not self._registers:
      return

    if self._default_caching_time < 1:
      # Do NOT use any caching on read
      self._registers = self._read_from_inverter(self._registers)
      self._cache_manager.save_to_cache(self._registers)
      return

    now = datetime.now()

    cached_registers: Dict[int, DeyeRegisterCacheData] = {}

    # Reset cache during the last and first 5 minutes of the day
    if_first_5_minutes = now.hour == 0 and now.minute <= 5
    if_last_5_minutes = now.hour == 23 and now.minute >= 55

    if if_first_5_minutes or if_last_5_minutes:
      if self._verbose:
        self._log.info(f'{self.name} resetting cache because midnight')
      self._cache_manager.reset_cache()
    else:
      cached_registers = self._cache_manager.get_cached_registers(self._registers)

    if self._verbose:
      registers_caching_time = {addr: reg.caching_time for addr, reg in self._registers.items()}
      self._log.info(f'{self.name} registers cache times: {registers_caching_time}')
      cached_data_map = {addr: reg.values for addr, reg in cached_registers.items()}
      self._log.info(f'{self.name} cached registers: {cached_data_map}')

    # Create a new dictionary containing only registers NOT found in cache
    uncached_registers = {addr: val for addr, val in self._registers.items() if addr not in cached_registers}

    if self._verbose:
      self._log.info(f'{self.name} uncached registers: {list(uncached_registers.keys())}')

    if uncached_registers:
      polled_registers = self._read_from_inverter(uncached_registers)
      self._cache_manager.save_to_cache(polled_registers)
      self._registers = {**cached_registers, **polled_registers}
    else:
      self._registers = cached_registers

  def _read_from_inverter(
    self,
    registers: Dict[int, DeyeRegisterCacheData],
  ) -> Dict[int, DeyeRegisterCacheData]:
    """Reads registers from inverter and returns a NEW dictionary with NEW objects."""
    if not registers:
      return {}

    groups = self._get_register_groups(registers)

    results: Dict[int, DeyeRegisterCacheData] = {}

    try:
      for group in groups:
        start = group[0].address
        last_item = group[-1]
        count = (last_item.address + last_item.quantity) - start

        data = self._solarman.read_holding_registers(address = start, quantity = count)

        for reg in group:
          offset = reg.address - start
          results[reg.address] = DeyeRegisterCacheData(
            address = reg.address,
            quantity = reg.quantity,
            caching_time = reg.caching_time,
            values = data[offset:offset + reg.quantity],
          )
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'error while reading registers: {self.name}') from e
    finally:
      self._solarman.disconnect()

    return results

  def write_registers_to_inverter(self) -> None:
    if not self._registers_to_write:
      return

    try:
      for reg in self._registers_to_write:
        result = self._solarman.write_multiple_holding_registers(reg.address, reg.values)
        if result != len(reg.values):
          raise RuntimeError(f'{self.name}: expected to write {len(reg.values)} values '
                             f'at address {reg.address}, but wrote {result}')

        # Update the local dictionary with the new object
        # This ensures subsequent reads within this session get the new value
        self._registers[reg.address] = reg

        # Update the persistent JSON cache
        self._cache_manager.save_to_cache({reg.address: reg})

      self._registers_to_write.clear()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'error while writing registers: {self.name}') from e
    finally:
      self._solarman.disconnect()

  def reset_cache(self) -> None:
    self._cache_manager.reset_cache()
