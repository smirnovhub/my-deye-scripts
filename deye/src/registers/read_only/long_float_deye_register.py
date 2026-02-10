from typing import Any, Optional

from datetime import timedelta

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
    caching_time: Optional[timedelta] = None,
    quantity: int = 2,
  ):
    super().__init__(
      address = address,
      name = name,
      description = description,
      suffix = suffix,
      avg = avg,
      caching_time = caching_time,
      quantity = quantity,
    )

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)
    return DeyeUtils.from_long_register_values(data, self.scale)
