from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_registers_section import DeyeWebRegistersSection
from deye_web_base_info_section import DeyeWebBaseInfoSection

class DeyeWebSettingsSection(DeyeWebBaseInfoSection):
  def __init__(self, sections: List[DeyeWebRegistersSection]):
    super().__init__(
      DeyeWebSection.settings,
      only_master = True,
    )
    self._sections = sections

  def build_registers_str(self, registers: List[DeyeRegister], on_click: str = '') -> str:
    result = ''

    for section in self._sections:
      for register in section.registers:
        tab_id = DeyeWebUtils.short(DeyeWebConstants.tab_template.format(section.section.id))
        page_id = DeyeWebUtils.short(DeyeWebConstants.page_template.format(section.section.id))
        on_click = f"openPage('{page_id}', '{tab_id}', true)"
        result += self.build_register(register.description, register, on_click)

    return result
