from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_registers import DeyeRegisters
from deye_web_base_select_section import DeyeWebBaseSelectSection

class DeyeWebMaxChargeCurrentSection(DeyeWebBaseSelectSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(DeyeWebSection.battery_max_charge_current)
    self._registers: List[DeyeRegister] = [
      registers.battery_max_charge_current_register,
    ]
