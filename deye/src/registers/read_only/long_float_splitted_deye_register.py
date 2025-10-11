from typing import List

from deye_utils import DeyeUtils
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

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
    self._split_offset = split_offset

  @property
  def addresses(self) -> List[int]:
    return [self.address, self.address + self._split_offset]

  def read_internal(self, interactor: DeyeModbusInteractor):
    data = interactor.read_register(self.address, self.quantity)
    value = DeyeUtils.from_long_register_values([data[0], data[self._split_offset]], self.scale)
    return value

  @property
  def scale(self) -> int:
    return 10

  @property
  def split_offset(self) -> int:
    return self._split_offset
