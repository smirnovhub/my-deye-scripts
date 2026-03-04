from typing import Any, List, Optional

from datetime import timedelta

from deye_utils import DeyeUtils
from long_float_deye_register import LongFloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class LongFloatSplittedDeyeRegister(LongFloatDeyeRegister):
  def __init__(
    self,
    address: int,
    split_offset: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
    caching_time: Optional[timedelta] = None,
  ):
    super().__init__(
      address = address,
      name = name,
      description = description,
      suffix = suffix,
      avg = avg,
      caching_time = caching_time,
      quantity = split_offset + 1,
    )
    self._split_offset = split_offset

  @property
  def addresses(self) -> List[int]:
    return [self.address, self.address + self._split_offset]

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)
    return DeyeUtils.from_long_register_values([data[0], data[self._split_offset]], self.scale)

  @property
  def split_offset(self) -> int:
    return self._split_offset
