from typing import Any

from deye_utils import DeyeUtils
from float_deye_register import FloatDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class SignedFloatDeyeRegister(FloatDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, name, description, suffix, avg)

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    data = interactor.read_register(self.address, self.quantity)
    return DeyeUtils.to_signed(data[0]) / self.scale
