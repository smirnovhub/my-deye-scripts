from typing import List
from functools import cached_property

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class DataCollectorRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @cached_property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.gen_port_mode_register,
      self.gen_power_register,
      self.load_power_register,
      self.battery_max_charge_current_register,
      self.battery_soc_register,
      self.battery_voltage_register,
      self.grid_external_ct_power_register,
      self.grid_state_register,
      self.grid_voltage_register,
      self.system_work_mode_register,
    ]
