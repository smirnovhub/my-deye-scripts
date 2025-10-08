import re

from datetime import datetime
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

from deye_utils import (
  to_bytes,
  to_inv_time,
)

class SystemTimeWritableDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, 3, name, description, suffix, avg)
    self._value = datetime(1970, 1, 1)

  @property
  def can_write(self) -> bool:
    return True

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    year, month, day, hour, minute, second = to_bytes(data)

    try:
      value = datetime(year + 2000, month, day, hour, minute, second)
    except ValueError:
      value = datetime(1970, 1, 1)

    return value

  def write(self, interactor: DeyeModbusInteractor, value):
    val = str(value)

    if not re.match(r'^\d{4}\-\d{2}\-\d{2}\s\d{2}\:\d{2}\:\d{2}$', val):
      self.error('write(): value doesn\'t match date/time format')

    year, month, day, hour, minute, second = [int(x) for x in re.split(r'[\-\:\s]', val)]

    if year < 2000:
      self.error(f'write(): year should be >= 2000')

    try:
      date = datetime(year, month, day, hour, minute, second)
    except ValueError as e:
      self.error(f'write(): {str(e)}')

    values = to_inv_time([year - 2000, month, day, hour, minute, second])

    if interactor.write_register(self.address, values) != len(values):
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = date
    return self._value
