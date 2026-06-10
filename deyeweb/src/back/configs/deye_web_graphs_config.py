from typing import List
from urllib.parse import urljoin

from env_utils import EnvUtils
from simple_singleton import singleton
from deye_register import DeyeRegister
from deye_web_constants import DeyeWebConstants

@singleton
class DeyeWebGraphsConfig:
  def __init__(self):
    registers = DeyeWebConstants.registers
    self._graphs_base_url = EnvUtils.get_deye_web_graphs_base_url()
    self._graphs_format = EnvUtils.get_deye_graphs_format()
    regs: List[DeyeRegister] = [
      registers.battery_current_register,
      registers.battery_power_register,
      registers.battery_soc_register,
      registers.battery_temperature_register,
      registers.gen_power_register,
      registers.grid_external_ct_power_register,
      registers.grid_internal_ct_power_register,
      registers.grid_state_register,
      registers.grid_voltage_register,
      registers.inverter_ac_temperature_register,
      registers.inverter_dc_temperature_register,
      registers.inverter_system_time_diff_register,
      registers.load_power_register,
      registers.pv1_power_register,
      registers.pv2_power_register,
      registers.pv_total_power_register,
    ]

    self._urls = {register.name: f"{register.name}.{self._graphs_format}" for register in regs}

  def get_url_for_register(self, register_name: str) -> str:
    if not self._graphs_base_url:
      return ''

    url = self._urls.get(register_name, '')
    return urljoin(self._graphs_base_url, url) if url else ''
