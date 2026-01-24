from typing import Dict, List

from simple_singleton import singleton
from deye_web_constants import DeyeWebConstants

@singleton
class DeyeWebSelectionsConfig:
  def __init__(self):
    registers = DeyeWebConstants.registers

    currents: List[float] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]

    self.selections: Dict[str, List[float]] = {
      registers.battery_gen_charge_current_register.name: currents,
      registers.battery_grid_charge_current_register.name: currents,
      registers.battery_max_charge_current_register.name: currents,
      registers.grid_charging_start_soc_register.name: [60, 65, 70, 75, 80, 85, 90, 93, 95, 97, 98, 100],
      registers.grid_connect_voltage_low_register.name: [210, 230],
      registers.grid_peak_shaving_power_register.name: [1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000],
      registers.grid_reconnection_time_register.name: [60, 120, 240, 300, 420, 480, 600, 720, 900],
      registers.time_of_use_power_register.name: [0, 125, 250, 500, 750, 1000, 1250, 1500, 2000, 2500, 2750, 3000],
      registers.time_of_use_soc_register.name: [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100],
    }

  def get_selections_for_register(self, register_name: str) -> List[float]:
    return self.selections.get(register_name, [])
