from typing import Any, List

from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_grid_state import DeyeGridState

class GridStateDeyeRegister(IntDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = address,
      name = name,
      description = description,
      suffix = suffix,
      avg = avg,
    )
    self._value = DeyeGridState.unknown

  def read(self, interactors: List[DeyeModbusInteractor]) -> Any:
    if self._avg == DeyeRegisterAverageType.none or len(interactors) == 1:
      self._value = self.read_from_master_interactor(interactors)
      return self._value

    self._value = DeyeGridState.on_grid
    for interactor in interactors:
      value = self.read_internal(interactor)
      if value != DeyeGridState.on_grid:
        self._value = DeyeGridState.off_grid

    return self._value

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    value = super().read_internal(interactor)
    for state in DeyeGridState:
      if value == state.value:
        return state
    return DeyeGridState.unknown
