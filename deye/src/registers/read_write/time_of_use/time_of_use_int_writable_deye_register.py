from typing import Any

from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from int_writable_deye_register import IntWritableDeyeRegister

class TimeOfUseIntWritableDeyeRegister(IntWritableDeyeRegister):
  def __init__(
    self,
    address: int,
    min_value: int,
    max_value: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, min_value, max_value, name, description, suffix, avg, 6)

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)
    # Without rounding, small floating-point errors (e.g. 3.334999...)
    # cause inconsistent results, making random-based tests fail unpredictably.
    # Rounding to 2 decimals ensures stable, repeatable test outcomes.
    return round(sum(data) / len(data))

  def write(self, interactor: DeyeModbusInteractor, value) -> Any:
    try:
      value = int(value)
    except Exception as e:
      self.error('write(): can\'t convert value to int')

    if value < self.min_value or value > self.max_value:
      self.error(f'write(): value should be from {self.min_value} to {self.max_value}')

    socs = [value] * self.quantity

    if interactor.write_register(self.address, socs) != len(socs):
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
