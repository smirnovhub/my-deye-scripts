from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class TemperatureDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, 1, name, description, suffix, avg)
    self._value = 0.0

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = interactor.read_register(self.address, self.quantity)[0]
    value = (value + self.shift) / self.scale
    return value

  @property
  def shift(self) -> int:
    return -1000

  @property
  def scale(self) -> int:
    return 10
