from typing import Any

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class FloatDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
    quantity: int = 1,
  ):
    super().__init__(address, quantity, name, description, suffix, avg)
    self._value = 0.0
    self._scale = 10

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)
    return data[0] / self.scale

  def with_scale(self, scale: int) -> DeyeRegister:
    self._scale = scale
    return self

  @property
  def scale(self) -> int:
    return self._scale
