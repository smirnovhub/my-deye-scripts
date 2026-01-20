from typing import Dict

from simple_singleton import singleton
from deye_web_constants import DeyeWebConstants

@singleton
class DeyeWebGraphsConfig:
  def __init__(self):
    self.base_path = '../solar/current_graphs'
    registers = DeyeWebConstants.registers

    self.urls: Dict[str, str] = {
      registers.battery_power_register.name: 'battery_power.png',
      registers.battery_soc_register.name: 'battery_soc.png',
      registers.battery_temperature_register.name: 'battery_temperature.png',
      registers.gen_power_register.name: 'gen_power.png',
      registers.grid_external_ct_power_register.name: 'grid_external_ct_power.png',
      registers.grid_internal_ct_power_register.name: 'grid_power.png',
      registers.grid_voltage_register.name: 'grid_voltage.png',
      registers.inverter_ac_temperature_register.name: 'inverter_ac_temperature.png',
      registers.inverter_dc_temperature_register.name: 'inverter_dc_temperature.png',
      registers.inverter_system_time_diff_register.name: 'inverter_system_time_diff.png',
      registers.load_power_register.name: 'load_power.png',
      registers.pv1_power_register.name: 'pv1_power.png',
      registers.pv2_power_register.name: 'pv2_power.png',
      registers.pv_total_power_register.name: 'pv_total_power.png',
    }

  def get_url_for_register(self, register_name: str) -> str:
    url = self.urls.get(register_name, '')
    return f'{self.base_path}/{url}' if url else ''
