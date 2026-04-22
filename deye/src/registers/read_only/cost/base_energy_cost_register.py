from typing import Dict, List

from deye_register import DeyeRegister
from deye_register_group import DeyeRegisterGroup
from float_deye_register import FloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class BaseEnergyCostRegister(FloatDeyeRegister):
  def __init__(
    self,
    energy_register: DeyeRegister,
    energy_costs: Dict[int, float],
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = 0,
      description = description,
      suffix = suffix,
      group = group,
      avg = avg,
      quantity = 0,
    )
    self._energy_register = energy_register
    self._energy_costs = energy_costs
    self._scale = 100

  @property
  def addresses(self) -> List[int]:
    return self._energy_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    self._energy_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]) -> None:
    self._energy_register.read(interactors)
    super().read(interactors)

  @property
  def energy_costs(self) -> Dict[int, float]:
    return self._energy_costs

  @property
  def current_energy_cost(self) -> float:
    if not self._energy_costs:
      return 0.0
    return list(self._energy_costs.values())[-1]

  @property
  def energy_register(self) -> DeyeRegister:
    return self._energy_register
