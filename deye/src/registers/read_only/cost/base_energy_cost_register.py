from typing import Any, Dict, List

from deye_register import DeyeRegister
from float_deye_register import FloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_energy_cost import DeyeEnergyCost
from deye_register_average_type import DeyeRegisterAverageType

class BaseEnergyCostRegister(FloatDeyeRegister):
  def __init__(
    self,
    energy_register: DeyeRegister,
    energy_costs: Dict[int, float],
    name: str,
    description: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(0, name, description, DeyeEnergyCost().currency_code, avg, 0)
    self._energy_register = energy_register
    self._energy_costs = energy_costs
    self._scale = 100

  @property
  def addresses(self) -> List[int]:
    return self._energy_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    self._energy_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]) -> Any:
    self._energy_register.read(interactors)
    return super().read(interactors)

  @property
  def energy_costs(self) -> Dict[int, float]:
    return self._energy_costs

  @property
  def current_energy_cost(self) -> float:
    return list(self._energy_costs.values())[-1]

  @property
  def energy_register(self) -> DeyeRegister:
    return self._energy_register
