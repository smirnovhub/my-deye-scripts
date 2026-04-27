from typing import Any

from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_group import DeyeRegisterGroup
from deye_register_average_type import DeyeRegisterAverageType
from deye_system_work_mode import DeyeSystemWorkMode

class SystemWorkModeWritableDeyeRegister(IntDeyeRegister):
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
    self._value = DeyeSystemWorkMode.unknown

  @property
  def can_write(self) -> bool:
    return True

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    value = super().read_internal(interactor)
    for mode in DeyeSystemWorkMode:
      if value == mode.value:
        return mode
    return DeyeSystemWorkMode.unknown

  def write(self, interactor: DeyeModbusInteractor, value: Any) -> None:
    if not isinstance(value, DeyeSystemWorkMode):
      self.error(f'write(): value should be of type {DeyeSystemWorkMode.__name__}')

    if value == DeyeSystemWorkMode.unknown:
      self.error(f'write(): icorrect value of {DeyeSystemWorkMode.__name__}')

    if value.value < 0:
      self.error(f'write(): value of {DeyeSystemWorkMode.__name__} should be >= 0')

    interactor.write_register(self.address, [value.value])

    self._value = value
