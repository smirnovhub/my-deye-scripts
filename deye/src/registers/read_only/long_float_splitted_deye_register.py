from typing import List
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_utils import get_long_register_value

class LongFloatSplittedDeyeRegister(BaseDeyeRegister):
  def __init__(self,
               address: int,
               split_offset: int,
               name: str,
               description: str,
               suffix: str,
               avg = DeyeRegisterAverageType.none):
    super().__init__(address, split_offset + 1, name, description, suffix, avg)
    self._value = 0.0
    self.split_offset = split_offset

  @property
  def addresses(self) -> List[int]:
    return [self.address, self.address + self.split_offset]

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    value = get_long_register_value([data[0], data[self.split_offset]], 10)
    return value
