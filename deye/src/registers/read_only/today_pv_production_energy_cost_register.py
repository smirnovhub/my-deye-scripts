from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_energy_cost import DeyeEnergyCost
from deye_register_average_type import DeyeRegisterAverageType

class TodayPvProductionEnergyCostRegister(BaseDeyeRegister):
  def __init__(self,
               pv_production_register: DeyeRegister,
               name: str,
               description: str,
               suffix: str,
               avg = DeyeRegisterAverageType.none):
    super().__init__(0, 0, name, description, suffix, avg)
    self._pv_production_register = pv_production_register

  @property
  def addresses(self) -> List[int]:
    return self._pv_production_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._pv_production_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._pv_production_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    energy_cost = DeyeEnergyCost()
    production = self._pv_production_register.value

    value = round(production * energy_cost.current_cost, 2)

    return value
