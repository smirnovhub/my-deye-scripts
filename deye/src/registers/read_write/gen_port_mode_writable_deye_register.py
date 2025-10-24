from typing import Any

from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_gen_port_mode import DeyeGenPortMode

class GenPortModeWritableDeyeRegister(IntDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, name, description, suffix, avg)
    self._register_type = DeyeGenPortMode
    self._value = self._register_type.unknown

  @property
  def can_write(self) -> bool:
    return True

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    value = super().read_internal(interactor)
    for mode in self._register_type:
      if value == mode.value:
        return mode
    return self._register_type.unknown

  def write(self, interactor: DeyeModbusInteractor, value) -> Any:
    if not isinstance(value, self._register_type):
      self.error(f'write(): value should be of type {self._register_type.__name__}')

    if value == self._register_type.unknown:
      self.error(f'write(): icorrect value of {self._register_type.__name__}')

    val = value.value
    if val < 0:
      self.error(f'write(): value of {self._register_type.__name__} should be >= 0')

    if interactor.write_register(self.address, [val]) != 1:
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
