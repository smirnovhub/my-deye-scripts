import logging

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_modbus_interactor import DeyeModbusInteractor
from deye_modbus_solarman_async import DeyeModbusSolarmanAsync
from deye_register_cache_data import DeyeRegisterCacheData
from deye_registers_base_cache_manager_async import DeyeRegistersBaseCacheManagerAsync
from deye_registers_local_cache_manager_async import DeyeRegistersLocalCacheManagerAsync
from deye_registers_remote_cache_manager_async import DeyeRegistersRemoteCacheManagerAsync

class DeyeModbusInteractorAsync(DeyeModbusInteractor):
  def __init__(self, logger: DeyeLogger, **kwargs):
    self._logger = logger
    self._loggers = DeyeLoggers()
    self._log = logging.getLogger()
    self._solarman = DeyeModbusSolarmanAsync(logger, **kwargs)
    self._registers: Dict[int, DeyeRegisterCacheData] = dict()
    self._registers_to_write: List[DeyeRegisterCacheData] = []
    self._verbose = bool(kwargs.get('verbose', False))
    self._default_caching_time = max(0, int(kwargs.get('caching_time', 3)))
    self._max_register_count = 120

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

  @property
  def name(self) -> str:
    return self._logger.name

  @property
  def is_master(self) -> bool:
    return self._logger.name == self._loggers.master.name

  def clear_registers_queue(self) -> None:
    self._registers.clear()

  def enqueue_register(
    self,
    address: int,
    quantity: int,
    caching_time: Optional[timedelta],
  ) -> None:
    cache_time = self._default_caching_time
    if cache_time > 0 and caching_time:
      cache_time = int(caching_time.total_seconds())

    self._registers[address] = DeyeRegisterCacheData(
      address = address,
      quantity = quantity,
      caching_time = cache_time,
    )

  async def process_enqueued_registers(self) -> None:
    if not self._registers:
      return

    if self._default_caching_time < 1:
      # Do NOT use any caching on read
      self._registers = await self._read_from_inverter(self._registers)
      await self._cache_manager.save_to_cache(self._registers)
      return

    now = datetime.now()

    cached_registers: Dict[int, DeyeRegisterCacheData] = {}

    # Reset cache during the first 5 minutes of the day
    if now.hour == 0 and now.minute < 5:
      if self._verbose:
        self._log.info(f'{self.name} resetting cache because midnight')
      await self._cache_manager.reset_cache()
    else:
      cached_registers = await self._cache_manager.get_cached_registers(self._registers)

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
      await self._cache_manager.save_to_cache(polled_registers)
      self._registers = {**cached_registers, **polled_registers}
    else:
      self._registers = cached_registers

  async def _read_from_inverter(
    self,
    registers: Dict[int, DeyeRegisterCacheData],
  ) -> Dict[int, DeyeRegisterCacheData]:
    """Reads registers from inverter and returns a NEW dictionary with NEW objects."""
    if not registers:
      return {}

    results: Dict[int, DeyeRegisterCacheData] = {}
    sorted_addrs = sorted(registers.keys())

    groups: List[List[DeyeRegisterCacheData]] = []
    current_group: List[DeyeRegisterCacheData] = []

    for addr in sorted_addrs:
      reg = registers[addr]
      if not current_group:
        current_group.append(reg)
        continue

      group_start = current_group[0].address
      block_end = reg.address + reg.quantity

      if (block_end - group_start) <= self._max_register_count:
        current_group.append(reg)
      else:
        groups.append(current_group)
        current_group = [reg]

    if current_group:
      groups.append(current_group)

    if self._verbose:
      simple_groups = [[reg.address for reg in group] for group in groups]
      grp = str(simple_groups).replace("], ", "],\n  ").replace("[[", "[\n  [").replace("]]", "]\n]")
      self._log.info(f'register groups to read from {self.name}:\n{grp}')

    try:
      for group in groups:
        start = group[0].address
        last_item = group[-1]
        count = (last_item.address + last_item.quantity) - start

        data = await self._solarman.read_holding_registers(address = start, quantity = count)

        for reg in group:
          offset = reg.address - start
          results[reg.address] = DeyeRegisterCacheData(
            address = reg.address,
            quantity = reg.quantity,
            caching_time = reg.caching_time,
            values = data[offset:offset + reg.quantity],
          )
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{self.name}: error while reading registers') from e
    finally:
      await self._solarman.disconnect()

    return results

  def read_register(self, address: int, quantity: int) -> List[int]:
    reg = self._registers.get(address)
    return reg.values[:quantity] if reg else [0] * quantity

  def write_register(self, address: int, values: List[int]) -> int:
    # Create a new data object for the updated register
    updated_register = DeyeRegisterCacheData(
      address = address,
      quantity = len(values),
      caching_time = self._default_caching_time,
      values = values,
    )

    self._registers_to_write.append(updated_register)
    return len(values)

  async def write_registers_to_inverter(self) -> None:
    if not self._registers_to_write:
      return

    try:
      for reg in self._registers_to_write:
        result = await self._solarman.write_multiple_holding_registers(reg.address, reg.values)
        if result != len(reg.values):
          raise RuntimeError(f'{self.name}: expected to write {len(reg.values)} values '
                             f'at address {reg.address}, but wrote {result}')

        # Update the local dictionary with the new object
        # This ensures subsequent reads within this session get the new value
        self._registers[reg.address] = reg

        # Update the persistent JSON cache
        await self._cache_manager.save_to_cache({reg.address: reg})

    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{self.name}: error while writing registers') from e
    finally:
      await self._solarman.disconnect()

  async def reset_cache(self) -> None:
    await self._cache_manager.reset_cache()

  def disconnect(self) -> None:
    self.clear_registers_queue()
