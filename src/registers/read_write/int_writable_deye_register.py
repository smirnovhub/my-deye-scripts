from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class IntWritableDeyeRegister(IntDeyeRegister):
  def __init__(self, address: int, min_value: int, max_value: int, name: str, description: str, suffix: str, avg = DeyeRegisterAverageType.none):
    super().__init__(address, name, description, suffix, avg)
    self._min_value = min_value
    self._max_value = max_value

  @property
  def can_write(self):
    return True

  def write(self, interactor: DeyeModbusInteractor, value):
    try:
      value = int(value)
    except Exception as e:
      self.error('write(): can\'t convert value to int')

    if value < self.min_value or value > self.max_value:
      self.error(f'write(): value should be from {self.min_value} to {self.max_value}')

    if interactor.write_register(self.address, [value]) != 1:
      self.error(f'write(): something went wrong while writing {self.description}')

    return value
