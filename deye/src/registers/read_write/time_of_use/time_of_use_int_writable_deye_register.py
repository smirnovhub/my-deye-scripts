from typing import Any

from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from int_writable_deye_register import IntWritableDeyeRegister

class TimeOfUseIntWritableDeyeRegister(IntWritableDeyeRegister):
  def __init__(
    self,
    address: int,
    min_value: int,
    max_value: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = address,
      min_value = min_value,
      max_value = max_value,
      description = description,
      suffix = suffix,
      group = group,
      avg = avg,
      quantity = 6,
    )

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    return interactor.read_register(self.address, self.quantity)

  def write(self, interactor: DeyeModbusInteractor, value: Any) -> None:
    # Check if the value is a list containing only integers
    if not isinstance(value, list) or not all(type(item) is int for item in value):
      self.error("Value must be a list of integers")

    if len(value) != self.quantity:
      self.error(f"Value should contain {self.quantity} elements")

    if not all(self.min_value <= v <= self.max_value for v in value):
      self.error(f'write(): all values should be from {self.min_value} to {self.max_value}')

    interactor.write_register(self.address, value)

    self._value = value
