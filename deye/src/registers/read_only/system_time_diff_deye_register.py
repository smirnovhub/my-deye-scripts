from typing import Any, List

from datetime import datetime

from deye_exceptions import DeyeValueException
from deye_register import DeyeRegister
from deye_utils import DeyeUtils
from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class SystemTimeDiffDeyeRegister(IntDeyeRegister):
  def __init__(
    self,
    system_time_register: DeyeRegister,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = 0,
      name = name,
      description = description,
      suffix = suffix,
      avg = avg,
      quantity = 0,
    )
    self._system_time_register = system_time_register

  @property
  def addresses(self) -> List[int]:
    return self._system_time_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    self._system_time_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]) -> Any:
    self._system_time_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    value = self._system_time_register.read_internal(interactor)
    if not isinstance(value, datetime):
      raise DeyeValueException(f"{type(self).__name__}.read_internal(): system time value should by of type 'datetime'")
    return int(round((value - DeyeUtils.get_current_time()).total_seconds()))

  @property
  def system_time_register(self) -> DeyeRegister:
    return self._system_time_register
