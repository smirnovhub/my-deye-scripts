from typing import List
from functools import cached_property

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class TimeOfUseRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @cached_property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.time_of_use_register,
      self.battery_low_batt_soc_register,
    ]
