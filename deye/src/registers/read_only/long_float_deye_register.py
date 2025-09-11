from deye_utils import *
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class LongFloatDeyeRegister(BaseDeyeRegister):
  def __init__(self, address: int, name: str, description: str, suffix: str, avg = DeyeRegisterAverageType.none):
    super().__init__(address, 2, name, description, suffix, avg)

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    value = get_long_register_value(data, 10)
    return value
