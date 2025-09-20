from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_energy_cost import DeyeEnergyCost
from deye_register_average_type import DeyeRegisterAverageType

class TotalGenEnergyCostRegister(BaseDeyeRegister):
  def __init__(self,
               gen_energy_register: DeyeRegister,
               name: str,
               description: str,
               avg = DeyeRegisterAverageType.none):
    self.energy_cost = DeyeEnergyCost()
    self._gen_energy_register = gen_energy_register
    super().__init__(0, 0, name, description, self.energy_cost.currency_code, avg)
    self._value = 0.0

  @property
  def addresses(self) -> List[int]:
    return self._gen_energy_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._gen_energy_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._gen_energy_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    total_cost = 0
    gen_energy = self._gen_energy_register.value

    for prod, cost in reversed(list(self.energy_cost.gen_energy_costs.items())):
      delta = gen_energy - prod
      total_cost += delta * cost
      gen_energy -= delta

    return round(total_cost)
