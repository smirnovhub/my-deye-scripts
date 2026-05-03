import random
from typing import Any, Optional
from datetime import timedelta

from base_deye_register import BaseDeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class Test1DeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    quantity: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    caching_time: Optional[timedelta] = None,
  ):
    super().__init__(
      address = address,
      quantity = quantity,
      description = description,
      suffix = suffix,
      group = group,
      caching_time = caching_time,
    )
    self._value = []

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    if not interactor.is_master and self._avg == DeyeRegisterAverageType.only_master:
      return

    start_addr = self.address
    end_target = self.address + self.quantity

    # To get ~100 random overlapping chunks, we pick 100 random starting points
    # and ensure they cover the whole range plus add random "noise"

    # First, ensure start and end are explicitly in our schedule
    seeds = {start_addr, max(start_addr, end_target - 1)}

    # Add random starting points until we have 100 unique chunks
    attempts = 0
    while len(seeds) < 100 and attempts < 1000:
      seeds.add(random.randint(start_addr, end_target - 1))
      attempts += 1

    # Process each seed to create an overlapping chunk
    for s_addr in seeds:
      # Calculate maximum possible quantity from this point
      limit = end_target - s_addr

      # If it's the very first address, make sure it has some length
      # If it's a random middle address, pick a random length that stays in bounds
      r_qty = random.randint(1, limit)

      interactor.enqueue_register(s_addr, r_qty, self.caching_time)

    # CRITICAL: The "Gap Filler"
    # This ensures that even if random chunks missed something, we cover the whole range
    # using the protocol's maximum efficiency (or just one big chunk if possible)
    current = start_addr
    while current < end_target:
      # We can use a fixed step or just cover the rest
      step = end_target - current
      interactor.enqueue_register(current, step, self.caching_time)
      current += step

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    return interactor.read_register(self.address, self.quantity)
