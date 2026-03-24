from typing import List
from functools import cached_property

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class BatterySettingsRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @cached_property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.battery_shutdown_soc_register,
      self.battery_low_batt_soc_register,
      self.battery_restart_soc_register,
    ]
