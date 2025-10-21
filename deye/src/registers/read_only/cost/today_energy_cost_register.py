from typing import Dict, List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_energy_cost import DeyeEnergyCost
from deye_register_average_type import DeyeRegisterAverageType

class TodayEnergyCostRegister(BaseDeyeRegister):
  def __init__(
    self,
    energy_register: DeyeRegister,
    energy_costs: Dict[int, float],
    name: str,
    description: str,
    avg = DeyeRegisterAverageType.none,
  ):
    cost = DeyeEnergyCost()
    self._energy_register = energy_register
    self._energy_costs = energy_costs
    super().__init__(0, 0, name, description, cost.currency_code, avg)
    self._value = 0.0

  @property
  def addresses(self) -> List[int]:
    return self._energy_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._energy_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._energy_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    energy = self._energy_register.value
    return round(energy * self.current_energy_cost, 2)

  @property
  def energy_costs(self) -> Dict[int, float]:
    return self._energy_costs

  @property
  def current_energy_cost(self) -> float:
    return list(self._energy_costs.values())[-1]

  @property
  def energy_register(self) -> DeyeRegister:
    return self._energy_register
