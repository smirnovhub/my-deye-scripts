from deye_utils import DeyeUtils
from float_deye_register import FloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class LongFloatDeyeRegister(FloatDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
    quantity: int = 2,
  ):
    super().__init__(address, name, description, suffix, avg, quantity)

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    return DeyeUtils.from_long_register_values(data, self.scale)
