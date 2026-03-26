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
      self.battery_current_register,
      self.battery_power_register,
      self.battery_soc_register,
      self.battery_temperature_register,
      self.battery_voltage_register,
      self.gen_power_register,
      self.grid_external_ct_power_register,
      self.grid_frequency_register,
      self.grid_internal_ct_power_register,
      self.grid_power_register,
      self.grid_state_code_register,
      self.grid_voltage_register,
      self.inverter_ac_temperature_register,
      self.inverter_dc_temperature_register,
      self.inverter_system_time_diff_register,
      self.load_frequency_register,
      self.load_power_register,
      self.load_voltage_register,
      self.pv1_current_register,
      self.pv1_power_register,
      self.pv1_voltage_register,
      self.pv2_current_register,
      self.pv2_power_register,
      self.pv2_voltage_register,
      self.pv_total_current_register,
      self.pv_total_power_register,
    ]
