from typing import List
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class ForecastRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.battery_capacity_register,
      self.battery_soc_register,
      self.battery_current_register,
      self.battery_power_register
    ]
