from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_energy_cost import DeyeEnergyCost
from deye_register_average_type import DeyeRegisterAverageType

class TodayEnergyCostBaseRegister(BaseDeyeRegister):
  def __init__(self,
               production_register: DeyeRegister,
               name: str,
               description: str,
               avg = DeyeRegisterAverageType.none):
    self.energy_cost = DeyeEnergyCost()
    self._production_register = production_register
    super().__init__(0, 0, name, description, self.energy_cost.currency_code, avg)
    self._value = 0.0

  @property
  def addresses(self) -> List[int]:
    return self._production_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._production_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._production_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    production = self._production_register.value
    return round(production * self.energy_cost.current_pv_energy_cost, 2)

  @property
  def production_register(self) -> DeyeRegister:
    return self._production_register
