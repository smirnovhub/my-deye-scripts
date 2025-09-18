from typing import List
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory

class TodayStatRegisters(DeyeRegistersFactory.get_registers_class()):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [
      self.today_production_register,
      self.today_gen_energy_register,
      self.today_load_consumption_register,
      self.today_grid_purchased_energy_register,
      self.today_grid_feed_in_energy_register,
      self.today_battery_charged_energy_register,
      self.today_battery_discharged_energy_register,
      self.today_production_cost_register,
    ]
