from typing import Any

from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_gen_port_mode import DeyeGenPortMode

class GenPortModeWritableDeyeRegister(IntDeyeRegister):
  def __init__(
    self,
    address: int,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = address,
      description = description,
      suffix = suffix,
      avg = avg,
    )
    self._value = DeyeGenPortMode.unknown

  @property
  def can_write(self) -> bool:
    return True

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    value = super().read_internal(interactor)
    for mode in DeyeGenPortMode:
      if value == mode.value:
        return mode
    return DeyeGenPortMode.unknown

  def write(self, interactor: DeyeModbusInteractor, value: Any) -> Any:
    if not isinstance(value, DeyeGenPortMode):
      self.error(f'write(): value should be of type {DeyeGenPortMode.__name__}')

    if value == DeyeGenPortMode.unknown:
      self.error(f'write(): icorrect value of {DeyeGenPortMode.__name__}')

    if value.value < 0:
      self.error(f'write(): value of {DeyeGenPortMode.__name__} should be >= 0')

    if interactor.write_register(self.address, [value.value]) != 1:
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
