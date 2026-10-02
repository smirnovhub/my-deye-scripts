from typing import Any, Optional

from datetime import timedelta

from base_deye_register import BaseDeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class SerialNumberDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    avg = DeyeRegisterAverageType.none,
    caching_time: Optional[timedelta] = None,
  ):
    super().__init__(
      address = address,
      quantity = 5,
      description = description,
      suffix = suffix,
      group = group,
      avg = avg,
      caching_time = caching_time,
    )

  @property
  def can_write(self) -> bool:
    return False

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)

    sn_chars = []

    for reg in data:
      high_byte = (reg >> 8) & 0xFF
      low_byte = reg & 0xFF

      # Filter out non-printable ASCII characters and null bytes
      if 32 <= high_byte <= 126:
        sn_chars.append(chr(high_byte))

      if 32 <= low_byte <= 126:
        sn_chars.append(chr(low_byte))

    return "".join(sn_chars).strip()
