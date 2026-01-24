from typing import List

from deye_register import DeyeRegister
from deye_loggers import DeyeLoggers
from deye_web_base_section import DeyeWebBaseSection
from deye_web_constants import DeyeWebConstants
from deye_web_section import DeyeWebSection

class DeyeWebRegistersSection(DeyeWebBaseSection):
  def __init__(self, section: DeyeWebSection, only_master: bool = False):
    super().__init__(section)
    self.loggers: DeyeLoggers = DeyeWebConstants.loggers
    self.only_master: bool = only_master
    self._registers: List[DeyeRegister] = []

  @property
  def registers(self) -> List[DeyeRegister]:
    return self._registers

  def build_tab_content(self) -> str:
    return self.build_registers(self._registers)

  def build_registers(self, registers: List[DeyeRegister]) -> str:
    raise NotImplementedError('build_registers() is not implemented')
