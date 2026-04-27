from typing import Any, List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class SumDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    registers: List[DeyeRegister],
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = 0,
      quantity = 0,
      description = description,
      suffix = suffix,
      group = group,
      avg = avg,
    )
    self._value = 0.0
    self._registers = registers

  @property
  def addresses(self) -> List[int]:
    addr_list = []
    for register in self._registers:
      addr_list.extend(register.addresses)
    return list(set(addr_list))

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    for register in self._registers:
      register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]) -> None:
    for register in self._registers:
      register.read(interactors)
    super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    return sum(register.value for register in self._registers)

  @property
  def nested_registers(self) -> List[DeyeRegister]:
    return self._registers
