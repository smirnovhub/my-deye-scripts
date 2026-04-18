import time

from typing import Dict

from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_modbus_interactor import DeyeModbusInteractor
from deye_modbus_solarman_async import DeyeModbusSolarmanAsync
from deye_register_cache_data import DeyeRegisterCacheData
from deye_registers_base_cache_manager_async import DeyeRegistersBaseCacheManagerAsync
from deye_registers_local_cache_manager_async import DeyeRegistersLocalCacheManagerAsync
from deye_registers_remote_cache_manager_async import DeyeRegistersRemoteCacheManagerAsync

class DeyeModbusInteractorAsync(DeyeModbusInteractor):
  def __init__(
    self,
    logger: DeyeLogger,
    **kwargs,
  ):
    super().__init__(
      logger = logger,
      **kwargs,
    )

    self._solarman = DeyeModbusSolarmanAsync(logger, **kwargs)

    # Initialize cache manager
    self._cache_manager: DeyeRegistersBaseCacheManagerAsync
    if self._loggers.remote_cache_server:
      self._cache_manager = DeyeRegistersRemoteCacheManagerAsync(
        name = self._logger.name,
        serial = self._logger.serial,
        remote_cache_server = self._loggers.remote_cache_server,
      )
    else:
      self._cache_manager = DeyeRegistersLocalCacheManagerAsync(
        name = self._logger.name,
        serial = self._logger.serial,
      )

  async def process_enqueued_registers(self) -> None:
    if not self._registers:
      return

    if self._default_caching_time < 1:
      # Do NOT use any caching on read
      self._registers = await self._read_from_inverter(self._registers)

      if self._can_cache():
        await self._cache_manager.save_to_cache(registers_to_save = self._registers)
      return

    cached_registers: Dict[int, DeyeRegisterCacheData] = {}

    if self._can_cache():
      cached_registers = await self._cache_manager.get_cached_registers(
        registers_to_check = self._registers,
        current_ts = time.time(),
      )
    else:
      # Reset cache during the last and first 5 minutes of the day
      if self._verbose:
        self._log.info(f'{self.name} resetting cache because midnight')
      await self._cache_manager.reset_cache()

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
      polled_registers = await self._read_from_inverter(uncached_registers)

      if self._can_cache():
        await self._cache_manager.save_to_cache(registers_to_save = polled_registers)
      self._registers = {**cached_registers, **polled_registers}
    else:
      self._registers = cached_registers

    DeyeModbusInteractor._TOTAL_REGISTERS_GOT_FROM_CACHE += len(cached_registers)
    DeyeModbusInteractor._TOTAL_REGISTERS_GOT_FROM_INVERTER += len(uncached_registers)

    self._log_cache_hit_rate()

  async def _read_from_inverter(
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

        data = await self._solarman.read_holding_registers(address = start, quantity = count)
        current_ts = time.time() # Should be exact after read_holding_registers() call

        if len(data) != count:
          raise RuntimeError(f'{self.name}: expected to read {count} values '
                             f'at address {start}, but got {len(data)}')

        for reg in group:
          offset = reg.address - start
          results[reg.address] = DeyeRegisterCacheData(
            address = reg.address,
            quantity = reg.quantity,
            caching_time = reg.caching_time,
            read_ts = current_ts,
            values = data[offset:offset + reg.quantity],
          )
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{self.name}: error while reading registers') from e
    finally:
      await self._solarman.disconnect()

    self._log.info(f'{self.name} got {len(results)} registers from inverter')

    return results

  async def write_registers_to_inverter(self) -> None:
    if not self._registers_to_write:
      return

    try:
      for reg in self._registers_to_write:
        result = await self._solarman.write_multiple_holding_registers(reg.address, reg.values)
        current_ts = time.time() # Should be exact after write_multiple_holding_registers() call

        if result != len(reg.values):
          raise RuntimeError(f'{self.name}: expected to write {len(reg.values)} values '
                             f'at address {reg.address}, but wrote {result}')

        # Update the local dictionary with the new object
        # This ensures subsequent reads within this session get the new value
        self._registers[reg.address] = reg

        updated_reg = DeyeRegisterCacheData(
          address = reg.address,
          quantity = reg.quantity,
          caching_time = reg.caching_time,
          read_ts = current_ts,
          values = reg.values,
        )

        # Update the persistent JSON cache
        if self._can_cache():
          await self._cache_manager.save_to_cache(registers_to_save = {reg.address: updated_reg})

      self._log.info(f'{self.name} wrote {len(self._registers_to_write)} registers to inverter')
      self._registers_to_write.clear()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{self.name}: error while writing registers') from e
    finally:
      await self._solarman.disconnect()

  async def reset_cache(self) -> None:
    await self._cache_manager.reset_cache()
