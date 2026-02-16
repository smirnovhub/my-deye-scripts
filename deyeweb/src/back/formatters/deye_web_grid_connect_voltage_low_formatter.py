from deye_web_constants import DeyeWebConstants
from deye_web_threshold_formatter import DeyeWebThresholdFormatter

class DeyeWebGridConnectVoltageLowFormatter(DeyeWebThresholdFormatter):
  def __init__(
    self,
    threshold1: float,
    threshold2: float,
  ):
    registers = DeyeWebConstants.registers
    super().__init__(
      threshold1,
      threshold2,
      colors = DeyeWebConstants.threshold_reversed_colors,
      # Needed by DeyeWebGridConnectVoltageLowSelectionBuilder
      used_registers = [
        registers.grid_power_register.name,
        registers.grid_state_register.name,
      ],
    )
