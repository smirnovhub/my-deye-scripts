from float_deye_register import FloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class FloatWritableDeyeRegister(FloatDeyeRegister):
  def __init__(
    self,
    address: int,
    min_value: float,
    max_value: float,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, name, description, suffix, avg)
    self._min_value = min_value
    self._max_value = max_value

  @property
  def can_write(self) -> bool:
    return True

  def write(self, interactor: DeyeModbusInteractor, value):
    try:
      value = float(value)
    except Exception as e:
      self.error('write(): can\'t convert value to float')

    if value < self.min_value or value > self.max_value:
      self.error(f'write(): value should be from {self.min_value} to {self.max_value}')

    value = int(round(value * self.scale))

    if interactor.write_register(self.address, [value]) != 1:
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value / self.scale
    return self._value
