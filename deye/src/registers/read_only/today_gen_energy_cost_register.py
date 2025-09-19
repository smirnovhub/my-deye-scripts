from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_energy_cost import DeyeEnergyCost
from deye_register_average_type import DeyeRegisterAverageType

class TodayGenEnergyCostRegister(BaseDeyeRegister):
  def __init__(self,
               gen_energy_register: DeyeRegister,
               name: str,
               description: str,
               avg = DeyeRegisterAverageType.none):
    self.energy_cost = DeyeEnergyCost()
    self._gen_energy_register = gen_energy_register
    super().__init__(0, 0, name, description, self.energy_cost.currency_code, avg)

  @property
  def addresses(self) -> List[int]:
    return self._gen_energy_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._gen_energy_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._gen_energy_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    gen_energy = self._gen_energy_register.value
    return round(gen_energy * self.energy_cost.current_gen_energy_cost, 2)
