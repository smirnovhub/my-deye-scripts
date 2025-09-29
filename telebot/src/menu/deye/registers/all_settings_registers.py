from typing import List
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory

class AllSettingsRegisters(DeyeRegistersFactory.get_registers_class()): # type: ignore
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.time_of_use_power_register,
      self.battery_max_charge_current_register,
      self.battery_max_discharge_current_register,
      self.battery_grid_charge_current_register,
      self.battery_gen_charge_current_register,
    ]
