from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_registers import DeyeRegisters
from deye_web_base_info_section import DeyeWebBaseInfoSection

class DeyeWebTotalSection(DeyeWebBaseInfoSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(DeyeWebSection.total)
    self._registers: List[DeyeRegister] = [
      registers.total_pv_production_register,
      registers.total_gen_energy_register,
      registers.total_load_consumption_register,
      registers.total_grid_purchased_energy_register,
      registers.total_grid_feed_in_energy_register,
      registers.total_battery_charged_energy_register,
      registers.total_battery_discharged_energy_register,
      registers.total_pv_production_cost_register,
      registers.total_gen_energy_cost_register,
      registers.total_grid_purchased_energy_cost_register,
    ]
