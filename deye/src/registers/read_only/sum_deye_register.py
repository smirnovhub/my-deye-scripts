from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class SumDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    registers: List[DeyeRegister],
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(0, 0, name, description, suffix, avg)
    self._value = 0.0
    self._registers = registers

  @property
  def addresses(self) -> List[int]:
    addr_list = []
    for register in self._registers:
      addr_list.extend(register.addresses)
    return list(set(addr_list))

  def enqueue(self, interactor: DeyeModbusInteractor):
    for register in self._registers:
      register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    for register in self._registers:
      register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    return sum(register.value for register in self._registers)

  @property
  def registers(self) -> List[DeyeRegister]:
    return self._registers
