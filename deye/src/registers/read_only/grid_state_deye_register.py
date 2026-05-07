from typing import Any, List

from int_deye_register import IntDeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_grid_state import DeyeGridState

class GridStateDeyeRegister(IntDeyeRegister):
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
    self._value = DeyeGridState.unknown

  def read(self, interactors: List[DeyeModbusInteractor]) -> None:
    if len(interactors) == 1:
      self._value = self.read_internal(interactors[0])
      return

    self._value = DeyeGridState.on_grid
    for interactor in interactors:
      value = self.read_internal(interactor)
      if value != DeyeGridState.on_grid:
        self._value = DeyeGridState.off_grid

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    value = super().read_internal(interactor)
    for state in DeyeGridState:
      if value == state.value:
        return state
    return DeyeGridState.unknown
