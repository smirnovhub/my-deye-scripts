from datetime import datetime
from system_time_writable_deye_register import SystemTimeWritableDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_exceptions import DeyeNotImplementedException

class SystemTimeDiffDeyeRegister(SystemTimeWritableDeyeRegister):
  def __init__(self, address: int, name: str, description: str, suffix: str, avg = DeyeRegisterAverageType.none):
    super().__init__(address, name, description, suffix, avg)

  @property
  def can_write(self) -> bool:
    return False

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = super().read_internal(interactor)
    now = datetime.now()
    value = round((value - now).total_seconds())
    return value

  def write(self, interactor: DeyeModbusInteractor, value):
    raise DeyeNotImplementedException(f'{type(self).__name__}.write() is not supported')
