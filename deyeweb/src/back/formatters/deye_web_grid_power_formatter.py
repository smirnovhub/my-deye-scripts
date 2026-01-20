from typing import Any

from deye_register import DeyeRegister
from deye_grid_state import DeyeGridState
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_threshold_formatter import DeyeWebThresholdFormatter

class DeyeWebGridPowerFormatter(DeyeWebThresholdFormatter):
  def __init__(
    self,
    threshold1: float,
    threshold2: float,
  ):
    super().__init__(
      threshold1,
      threshold2,
      DeyeWebConstants.threshold_reversed_colors,
    )

  def get_register_value(self, register: DeyeRegister) -> Any:
    return abs(register.value)

  def get_color(self, registers: DeyeRegisters, register: DeyeRegister) -> DeyeWebColor:
    grid_state = registers.grid_state_register.value
    if grid_state == DeyeGridState.on_grid:
      return super().get_color(registers, register)
    return DeyeWebColor.gray
