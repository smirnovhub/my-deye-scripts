from typing import Any, Dict

from deye_register import DeyeRegister
from base_energy_cost_register import BaseEnergyCostRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class TodayEnergyCostRegister(BaseEnergyCostRegister):
  def __init__(
    self,
    energy_register: DeyeRegister,
    energy_costs: Dict[int, float],
    name: str,
    description: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      energy_register = energy_register,
      energy_costs = energy_costs,
      name = name,
      description = description,
      avg = avg,
    )

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    energy = self._energy_register.value
    return round(energy * self.current_energy_cost, 2)
