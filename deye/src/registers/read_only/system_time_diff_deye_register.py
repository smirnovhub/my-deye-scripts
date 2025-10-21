from typing import List

from deye_utils import DeyeUtils
from system_time_writable_deye_register import SystemTimeWritableDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_exceptions import DeyeNotImplementedException

class SystemTimeDiffDeyeRegister(SystemTimeWritableDeyeRegister):
  def __init__(self, address: int, name: str, description: str, suffix: str, avg = DeyeRegisterAverageType.none):
    super().__init__(address, name, description, suffix, avg)
    self._value = 0

  @property
  def can_write(self) -> bool:
    return False

  def read(self, interactors: List[DeyeModbusInteractor]):
    value = super().read(interactors)
    self._value = round(value)
    return self._value

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = super().read_internal(interactor)
    return int(round((value - DeyeUtils.get_current_time()).total_seconds()))

  def write(self, interactor: DeyeModbusInteractor, value):
    raise DeyeNotImplementedException(f'{type(self).__name__}.write() is not supported')
