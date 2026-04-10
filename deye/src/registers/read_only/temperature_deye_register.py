from typing import Any

from float_deye_register import FloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_group import DeyeRegisterGroup
from deye_register_average_type import DeyeRegisterAverageType

class TemperatureDeyeRegister(FloatDeyeRegister):
  def __init__(
    self,
    address: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = address,
      description = description,
      suffix = suffix,
      group = group,
      avg = avg,
    )

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)
    return (data[0] + self.shift) / self.scale

  @property
  def shift(self) -> int:
    return -1000
