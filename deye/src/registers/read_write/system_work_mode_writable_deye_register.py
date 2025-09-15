from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_system_work_mode import DeyeSystemWorkMode

class SystemWorkModeWritableDeyeRegister(IntDeyeRegister):
  def __init__(self, address: int, name: str, description: str, suffix: str, avg = DeyeRegisterAverageType.none):
    super().__init__(address, name, description, suffix, avg)

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = super().read_internal(interactor)
    for mode in DeyeSystemWorkMode:
      if value == mode.value:
        return mode
    return DeyeSystemWorkMode.unknown

  def write(self, interactor: DeyeModbusInteractor, value):
    if not isinstance(value, DeyeSystemWorkMode):
      self.error('write(): value should be of type DeyeSystemWorkMode')

    val = value.value
    if val < 0:
      self.error('write(): value should be > 0')

    if interactor.write_register(self.address, [val]) != 1:
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
