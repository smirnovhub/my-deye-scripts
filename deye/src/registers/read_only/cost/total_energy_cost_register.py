from typing import Dict

from deye_register import DeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from today_energy_cost_register import TodayEnergyCostRegister

class TotalEnergyCostRegister(TodayEnergyCostRegister):
  def __init__(
    self,
    energy_register: DeyeRegister,
    energy_costs: Dict[int, float],
    name: str,
    description: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(energy_register, energy_costs, name, description, avg)

  def read_internal(self, interactor: DeyeModbusInteractor):
    total_cost = 0.0
    energy = self.energy_register.value

    for en, cost in reversed(list(self.energy_costs.items())):
      delta = energy - en
      total_cost += delta * cost
      energy -= delta

    return round(total_cost, 2)
