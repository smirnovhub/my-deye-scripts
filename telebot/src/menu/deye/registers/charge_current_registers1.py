from typing import List
from functools import cached_property

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class ChargeCurrentRegisters1(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @cached_property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.battery_soc_register,
      self.time_of_use_soc_register,
    ]
