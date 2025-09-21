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
    self._value = ''

  @property
  def can_write(self) -> bool:
    return True

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    as_bytes = to_bytes(data)

    try:
      value = datetime(
        2000 + as_bytes[0],
        as_bytes[1],
        as_bytes[2],
        as_bytes[3],
        as_bytes[4],
        as_bytes[5],
      )
    except:
      value = datetime(
        1970,
        1,
        1,
        0,
        0,
      )

    return value

  def write(self, interactor: DeyeModbusInteractor, value):
    try:
      value = str(value)
    except Exception as e:
      self.error('write(): can\'t convert value to str')

    if not re.match(r'^\d{4}\-\d{2}\-\d{2}\s\d{2}\:\d{2}\:\d{2}$', value):
      self.error('write(): value doesn\'t match date/time format')

    as_ints = [int(x) for x in re.split(r'[\-\:\s]', value)]
    now = datetime.now()

    if as_ints[0] != now.year:
      self.error('write(): year is wrong')

    if as_ints[1] != now.month:
      self.error('write(): month is wrong')

    if as_ints[2] != now.day:
      self.error('write(): day is wrong')

    as_ints[0] -= 2000
    values = to_inv_time(as_ints)

    if interactor.write_register(self.address, values) != len(values):
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
