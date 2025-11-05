from typing import Any

from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor

class TestDeyeRegister(BaseDeyeRegister):
  def __init__(self, address: int, quantity: int, name: str, description: str, suffix: str):
    super().__init__(address, quantity, name, description, suffix)
    self._value = 0

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    values = interactor.read_register(self.address, self.quantity)

    for idx, x in enumerate(values):
      print(self.address + idx, '=', x)

    value = 0
    return value
