from typing import List
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class DeyeWebForecastRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.battery_soc_register,
      self.battery_capacity_register,
      self.battery_current_register,
      self.battery_power_register,
      self.time_of_use_power_register,
      self.battery_max_charge_current_register,
      self.battery_max_discharge_current_register,
    ]
