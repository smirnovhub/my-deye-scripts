from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class FloatDeyeRegister(BaseDeyeRegister):
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
    self._scale = 10

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = interactor.read_register(self.address, self.quantity)[0] / self.scale
    return value

  def with_scale(self, scale: int):
    self._scale = scale
    return self
