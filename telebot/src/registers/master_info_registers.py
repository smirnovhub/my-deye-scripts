from typing import List
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class MasterInfoRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.battery_soc_register,
      self.battery_soh_register,
      self.battery_power_register,
      self.grid_state_register,
      self.grid_voltage_register,
      self.grid_internal_ct_power_register,
      self.grid_external_ct_power_register,
      self.load_power_register,
      self.pv1_power_register,
      self.gen_power_register,
      self.inverter_ac_temperature_register,
      self.inverter_dc_temperature_register,
      self.battery_temperature_register,
      self.inverter_system_time_diff_register
    ]
