from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_system_work_mode import DeyeSystemWorkMode

class SystemWorkModeWritableDeyeRegister(IntDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, name, description, suffix, avg)
    self._value = DeyeSystemWorkMode.unknown

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = super().read_internal(interactor)
    for mode in DeyeSystemWorkMode:
      if value == mode.value:
        return mode
    return DeyeSystemWorkMode.unknown

  @property
  def can_write(self) -> bool:
    return True

  def write(self, interactor: DeyeModbusInteractor, value):
    register_type = DeyeSystemWorkMode

    if isinstance(value, str):
      for mode in register_type:
        if str(mode) == value:
          value = mode
          break

      if not isinstance(value, register_type):
        self.error(f'write(): icorrect value of {register_type.__name__}')

    if not isinstance(value, register_type):
      self.error(f'write(): value should be of type {register_type.__name__}')

    if value == register_type.unknown:
      self.error(f'write(): icorrect value of {register_type.__name__}')

    val = value.value
    if val < 0:
      self.error('write(): value should be >= 0')

    if interactor.write_register(self.address, [val]) != 1:
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
