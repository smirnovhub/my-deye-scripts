from daytime_utils import DayTimeUtils
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from gps_coordinates import GpsCoordinates
from deye_web_threshold_formatter import DeyeWebThresholdFormatter

class DeyeWebPvPowerFormatter(DeyeWebThresholdFormatter):
  def __init__(
    self,
    threshold1: float,
    threshold2: float,
  ):
    super().__init__(
      threshold1,
      threshold2,
      DeyeWebConstants.threshold_colors,
      will_affect_tab_color = False,
    )

    self.daytime_utils = DayTimeUtils(GpsCoordinates.latitude, GpsCoordinates.longitude)

  def get_color(self, registers: DeyeRegisters, register: DeyeRegister) -> DeyeWebColor:
    if self.daytime_utils.is_day_time():
      return super().get_color(registers, register)
    return DeyeWebColor.gray
