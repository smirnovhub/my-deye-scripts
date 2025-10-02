from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class TimeOfUseIntWritableDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    min_value: int,
    max_value: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, 6, name, description, suffix, avg)
    self._value = 0.0
    self._min_value = min_value
    self._max_value = max_value

  @property
  def can_write(self) -> bool:
    return True

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    return sum(data) / len(data)

  def write(self, interactor: DeyeModbusInteractor, value):
    try:
      value = int(value)
    except Exception as e:
      self.error('write(): can\'t convert value to int')

    if value < self.min_value or value > self.max_value:
      self.error(f'write(): value should be from {self.min_value} to {self.max_value}')

    socs = [value] * self.quantity

    if interactor.write_register(self.address, socs) != len(socs):
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
