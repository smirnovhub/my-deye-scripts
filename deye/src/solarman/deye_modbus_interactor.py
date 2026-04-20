import logging

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_register_cache_data import DeyeRegisterCacheData
from deye_register_cache_hit_rate import DeyeRegisterCacheHitRate

class DeyeModbusInteractor:
  def __init__(
    self,
    logger: DeyeLogger,
    **kwargs,
  ):
    if type(self) is DeyeModbusInteractor:
      raise TypeError("DeyeModbusInteractor cannot be instantiated directly")

    self._logger = logger
    self._loggers = DeyeLoggers()
    self._log = logging.getLogger()
    self._registers: Dict[int, DeyeRegisterCacheData] = dict()
    self._registers_to_write: List[DeyeRegisterCacheData] = []
    self._verbose = bool(kwargs.get('verbose', False))
    self._default_caching_time = max(0, int(kwargs.get('caching_time', 3)))
    self._max_register_count = 120
    self._cache_hit_rate: DeyeRegisterCacheHitRate = DeyeRegisterCacheHitRate.zero()

  @property
  def name(self) -> str:
    return self._logger.name

  @property
  def is_master(self) -> bool:
    return self._logger.name == self._loggers.master.name

  @property
  def cache_hit_rate(self) -> DeyeRegisterCacheHitRate:
    return self._cache_hit_rate

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

  def _get_register_groups(
    self,
    registers: Dict[int, DeyeRegisterCacheData],
  ) -> List[List[DeyeRegisterCacheData]]:
    groups: List[List[DeyeRegisterCacheData]] = []
    current_group: List[DeyeRegisterCacheData] = []

    sorted_addrs = sorted(registers.keys())

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

    return groups

  def _can_cache(self) -> bool:
    now = datetime.now()
    if_first_minutes = now.hour == 0 and now.minute <= 5
    if_last_minutes = now.hour == 23 and now.minute >= 55
    return not if_first_minutes and not if_last_minutes

  def disconnect(self) -> None:
    self._registers.clear()
    self._registers_to_write.clear()
