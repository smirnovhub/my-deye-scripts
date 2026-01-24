from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_registers import DeyeRegisters
from deye_web_base_info_section import DeyeWebBaseInfoSection

class DeyeWebInfoSection(DeyeWebBaseInfoSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(DeyeWebSection.info)
    self._registers: List[DeyeRegister] = [
      registers.grid_state_register,
      registers.grid_voltage_register,
      registers.battery_soc_register,
      registers.battery_power_register,
      registers.grid_internal_ct_power_register,
      registers.grid_external_ct_power_register,
      registers.load_power_register,
      registers.pv1_power_register,
      registers.gen_power_register,
      registers.inverter_ac_temperature_register,
      registers.inverter_dc_temperature_register,
      registers.battery_temperature_register,
      registers.inverter_system_time_diff_register,
    ]
