from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class TemperatureDeyeRegister(BaseDeyeRegister):
  def __init__(self, address: int, name: str, description: str, suffix: str, avg = DeyeRegisterAverageType.none):
    super().__init__(address, 1, name, description, suffix, avg)

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = interactor.read_register(self.address, self.quantity)[0]
    value = (value - 1000) / 10
    return value
