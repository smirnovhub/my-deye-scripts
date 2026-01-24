from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_registers import DeyeRegisters
from deye_web_base_select_section import DeyeWebBaseSelectSection

class DeyeWebTimeOfUseSocSection(DeyeWebBaseSelectSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(DeyeWebSection.time_of_use_soc)
    self._registers: List[DeyeRegister] = [
      registers.time_of_use_soc_register,
    ]
