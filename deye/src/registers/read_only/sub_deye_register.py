from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor

class SubDeyeRegister(BaseDeyeRegister):
  def __init__(self, registers: List[DeyeRegister], name: str, description: str, suffix: str):
    super().__init__(0, 0, name, description, suffix)
    self._registers = registers

  @property
  def addresses(self):
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
    val = self._registers[0].value
    for register in self._registers[1:]:
      val -= register.value
    value = round(val, 1) if type(val) is float else val
    return value
