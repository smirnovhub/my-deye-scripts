from typing import Dict, List, Optional

from datetime import timedelta

from deye_file_lock import DeyeFileLock
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_modbus_solarman import DeyeModbusSolarman
from deye_register_cache_data import DeyeRegisterCacheData
from deye_registers_cache_manager import DeyeRegistersCacheManager
from deye_utils import DeyeUtils

class DeyeModbusInteractor:
  def __init__(self, logger: DeyeLogger, **kwargs):
    self.logger = logger
    self.loggers = DeyeLoggers()
    self.solarman = DeyeModbusSolarman(logger, **kwargs)
    self.registers: Dict[int, DeyeRegisterCacheData] = dict()
    self.verbose = bool(kwargs.get('verbose', False))
    self.default_caching_time = max(0, int(kwargs.get('caching_time', 3)))
    self.max_register_count = 120

    # Ensure cache directory exists
    DeyeUtils.ensure_dir_exists(DeyeFileLock.lock_path, mode = 0o777)

    # Initialize cache manager
    self.cache_manager = DeyeRegistersCacheManager(
      self.logger.name,
      DeyeFileLock.lock_path,
      verbose = self.verbose,
    )

  @property
  def name(self) -> str:
    return self.logger.name

  @property
  def is_master(self) -> bool:
    return self.logger.name == self.loggers.master.name

  def clear_registers_queue(self) -> None:
    self.registers.clear()

  def enqueue_register(
    self,
    address: int,
    quantity: int,
    caching_time: Optional[timedelta],
  ) -> None:
    cache_time = self.default_caching_time
    if cache_time > 0 and caching_time:
      cache_time = int(caching_time.total_seconds())

    self.registers[address] = DeyeRegisterCacheData(
      address = address,
      quantity = quantity,
      cache_time = cache_time,
    )

  def process_enqueued_registers(self) -> None:
    if not self.registers:
      return

    if self.default_caching_time < 1:
      # Do NOT use any caching on read
      self.registers = self.read_from_inverter(self.registers)
      self.cache_manager.save_to_cache(self.registers)
      return

    cached_registers = self.cache_manager.get_cached_registers(self.registers)

    if self.verbose:
      registers_cache_time = {addr: reg.cache_time for addr, reg in self.registers.items()}
      print(f'{self.name} registers cache times: {registers_cache_time}')
      cached_data_map = {addr: reg.values for addr, reg in cached_registers.items()}
      print(f'{self.name} cached registers: {cached_data_map}')

    # Create a new dictionary containing only registers NOT found in cache
    uncached_registers = {addr: val for addr, val in self.registers.items() if addr not in cached_registers}

    if self.verbose:
      print(f'{self.name} uncached registers: {list(uncached_registers.keys())}')

    if uncached_registers:
      polled_registers = self.read_from_inverter(uncached_registers)
      self.cache_manager.save_to_cache(polled_registers)
      self.registers = {**cached_registers, **polled_registers}
    else:
      self.registers = cached_registers

  def read_from_inverter(
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

      if (block_end - group_start) <= self.max_register_count:
        current_group.append(reg)
      else:
        groups.append(current_group)
        current_group = [reg]

    if current_group:
      groups.append(current_group)

    if self.verbose:
      simple_groups = [[reg.address for reg in group] for group in groups]
      grp = str(simple_groups).replace("], ", "],\n  ").replace("[[", "[\n  [").replace("]]", "]\n]")
      print(f'register groups to read from {self.name}:\n{grp}')

    try:
      for group in groups:
        start = group[0].address
        last_item = group[-1]
        count = (last_item.address + last_item.quantity) - start

        data = self.solarman.read_holding_registers(address = start, quantity = count)

        for reg in group:
          offset = reg.address - start
          results[reg.address] = DeyeRegisterCacheData(
            address = reg.address,
            quantity = reg.quantity,
            cache_time = reg.cache_time,
            values = data[offset:offset + reg.quantity],
          )
    finally:
      self.solarman.disconnect()

    return results

  def read_register(self, address: int, quantity: int) -> List[int]:
    reg = self.registers.get(address)
    return reg.values[:quantity] if reg else [0] * quantity

  def write_register(self, address: int, values: List[int]) -> int:
    try:
      result = self.solarman.write_multiple_holding_registers(address, values)
    finally:
      self.solarman.disconnect()

    # Create a new data object for the updated register
    updated_register = DeyeRegisterCacheData(
      address = address,
      quantity = len(values),
      cache_time = self.default_caching_time,
      values = values,
    )

    # Update the local dictionary with the new object
    # This ensures subsequent reads within this session get the new value
    self.registers[address] = updated_register

    # Update the persistent JSON cache
    self.cache_manager.save_to_cache({address: updated_register})

    return result

  # Deprecated
  def disconnect(self) -> None:
    self.clear_registers_queue()
