from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_registers import DeyeRegisters
from deye_web_base_select_section import DeyeWebBaseSelectSection

class DeyeWebGridPeakShavingPowerSection(DeyeWebBaseSelectSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(DeyeWebSection.grid_peak_shaving_power)
    self._registers: List[DeyeRegister] = [
      registers.grid_peak_shaving_power_register,
    ]
