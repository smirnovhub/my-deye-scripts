from typing import List

from deye_register import DeyeRegister
from deye_web_constants import DeyeWebConstants
from deye_web_registers_section import DeyeWebRegistersSection
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils

class DeyeWebBaseSelectSection(DeyeWebRegistersSection):
  def __init__(self, section: DeyeWebSection):
    super().__init__(section)

  def build_registers(self, registers: List[DeyeRegister]) -> str:
    result = ''
    for register in registers:
      result += self.build_register_with_selection(self.loggers.master.name, register)

    id = DeyeWebUtils.short(DeyeWebConstants.page_template.format(self.section.id))

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <div id="{id}" class="tabcontent">
        {result}
      </div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()

  def build_register_with_selection(self, prefix: str, register: DeyeRegister) -> str:
    id3 = DeyeWebUtils.short(f'{register.name}_list_field')
    id4 = DeyeWebUtils.short(DeyeWebConstants.selection_list_template.format(prefix, register.name))

    style_id = self.style_manager.register_style(DeyeWebConstants.flex_center_style)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <center>
        <div id="{id3}" class="{DeyeWebConstants.remote_data_with_spinner_name}"
          data-remote_field="{id4}">
        </div>
        <br>
        <div class="{style_id} counter">&nbsp;</div>
      </center>
      {DeyeWebUtils.end_comment(self)}
    """.strip()
