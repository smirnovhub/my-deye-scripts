from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_registers import DeyeRegisters
from deye_web_base_info_section import DeyeWebBaseInfoSection

class DeyeWebTodaySection(DeyeWebBaseInfoSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(DeyeWebSection.today)
    self._registers: List[DeyeRegister] = [
      registers.today_pv_production_register,
      registers.today_gen_energy_register,
      registers.today_load_consumption_register,
      registers.today_grid_purchased_energy_register,
      registers.today_grid_feed_in_energy_register,
      registers.today_battery_charged_energy_register,
      registers.today_battery_discharged_energy_register,
      registers.today_pv_production_cost_register,
      registers.today_gen_energy_cost_register,
      registers.today_grid_purchased_energy_cost_register,
    ]
