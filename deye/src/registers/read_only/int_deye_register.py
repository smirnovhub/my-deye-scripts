from typing import Any, Optional

from datetime import timedelta

from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class IntDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
    caching_time: Optional[timedelta] = None,
    quantity: int = 1,
  ):
    super().__init__(
      address = address,
      quantity = quantity,
      name = name,
      description = description,
      suffix = suffix,
      avg = avg,
      caching_time = caching_time,
    )
    self._value = 0

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)
    return data[0]
