from typing import Any

from int_deye_register import IntDeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class IntWritableDeyeRegister(IntDeyeRegister):
  def __init__(
    self,
    address: int,
    min_value: int,
    max_value: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    avg = DeyeRegisterAverageType.none,
    quantity: int = 1,
  ):
    super().__init__(
      address = address,
      description = description,
      suffix = suffix,
      group = group,
      avg = avg,
      quantity = quantity,
    )
    self._min_value = min_value
    self._max_value = max_value

  @property
  def can_write(self) -> bool:
    return True

  def write(self, interactor: DeyeModbusInteractor, value: Any) -> None:
    try:
      value = int(value)
    except Exception:
      self.error("write(): can't convert value to int")

    if value < self.min_value or value > self.max_value:
      self.error(f'write(): value should be from {self.min_value} to {self.max_value}')

    interactor.write_register(self.address, [value])

    self._value = value
