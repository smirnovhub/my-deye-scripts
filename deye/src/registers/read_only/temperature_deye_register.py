from float_deye_register import FloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class TemperatureDeyeRegister(FloatDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, name, description, suffix, avg)

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    return (data[0] + self.shift) / self.scale

  @property
  def shift(self) -> int:
    return -1000
