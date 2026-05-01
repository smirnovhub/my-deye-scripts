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
    self._registers_to_write: Dict[int, DeyeRegisterCacheData] = dict()
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
    if reg and len(reg.values) >= quantity:
      return reg.values[:quantity]

    # Initialize the result array with zeros of the requested size
    result = [0] * quantity
    requested_end = address + quantity

    # Iterate through all available registers to find overlaps
    for reg_addr, reg in self._registers.items():
      reg_end = reg_addr + reg.quantity

      # Check if current register overlaps with the requested range
      # Overlap exists if: (start1 < end2) AND (end1 > start2)
      if address < reg_end and requested_end > reg_addr:
        # Determine the intersection range
        intersect_start = max(address, reg_addr)
        intersect_end = min(requested_end, reg_end)

        # Calculate offsets
        # Where to take from in the source register
        src_offset = intersect_start - reg_addr
        # Where to put in the result array
        dest_offset = intersect_start - address

        # Number of registers to copy in this intersection
        copy_len = intersect_end - intersect_start

        # Map the values into the result array
        result[dest_offset:dest_offset + copy_len] = reg.values[src_offset:src_offset + copy_len]

    return result

  def write_register(self, address: int, values: List[int]) -> None:
    # Create a new data object for the updated register
    updated_register = DeyeRegisterCacheData(
      address = address,
      quantity = len(values),
      caching_time = self._default_caching_time,
      values = values,
    )

    self._registers_to_write[address] = updated_register

  def _get_register_groups(
    self,
    registers: Dict[int, DeyeRegisterCacheData],
  ) -> List[List[DeyeRegisterCacheData]]:
    if not registers:
      return []

    groups: List[List[DeyeRegisterCacheData]] = []
    current_group: List[DeyeRegisterCacheData] = []

    # Sort registers by starting address to process them linearly
    sorted_addrs = sorted(registers.keys())
    sorted_regs = [registers[addr] for addr in sorted_addrs]

    # Initialize trackers for the current physical block
    group_start = -1
    current_max_end = -1

    for reg in sorted_regs:
      reg_end = reg.address + reg.quantity

      # Start the very first group
      if not current_group:
        current_group.append(reg)
        group_start = reg.address
        current_max_end = reg_end
        continue

      # Check if this register is already fully covered by the current range
      if reg.address >= group_start and reg_end <= current_max_end:
        # Skip adding to physical read list, but keep it for data mapping logic if needed
        # For now, we skip it to avoid redundant bus commands
        continue

      # Check if expanding to this register stays within max_count
      potential_end = max(current_max_end, reg_end)

      if (potential_end - group_start) <= self._max_register_count:
        current_group.append(reg)
        current_max_end = potential_end
      else:
        # Gap too large or exceeds max_count, finalize current group
        groups.append(current_group)
        current_group = [reg]
        group_start = reg.address
        current_max_end = reg_end

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
