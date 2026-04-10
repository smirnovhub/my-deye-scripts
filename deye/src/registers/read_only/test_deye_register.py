from typing import Any

from base_deye_register import BaseDeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor

class TestDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    quantity: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
  ):
    super().__init__(
      address = address,
      quantity = quantity,
      description = description,
      suffix = suffix,
      group = group,
    )
    self._value = 0

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    values = interactor.read_register(self.address, self.quantity)

    for idx, x in enumerate(values):
      print(self.address + idx, '=', x)

    value = 0
    return value
