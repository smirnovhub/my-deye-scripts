from typing import List
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class TodayStatRegisters(DeyeRegisters):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.today_pv_production_register,
      self.today_gen_energy_register,
      self.today_load_consumption_register,
      self.today_grid_purchased_energy_register,
      self.today_grid_feed_in_energy_register,
      self.today_battery_charged_energy_register,
      self.today_battery_discharged_energy_register,
      self.today_pv_production_cost_register,
      self.today_grid_purchased_energy_cost_register,
      self.today_gen_energy_cost_register,
    ]
