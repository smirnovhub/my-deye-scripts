from typing import List

from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_registers_section import DeyeWebRegistersSection
from deye_register_average_type import DeyeRegisterAverageType

class DeyeWebBaseInfoSection(DeyeWebRegistersSection):
  def __init__(self, section: DeyeWebSection, only_master: bool = False):
    super().__init__(section, only_master)

  def build_registers_str(self, registers: List[DeyeRegister]) -> str:
    result = ''
    for register in registers:
      result += self.build_register(register.description, register)
    return result

  def build_registers(self, registers: List[DeyeRegister]) -> str:
    id = DeyeWebUtils.short(DeyeWebConstants.page_template.format(self.section.id))

    style_id1 = self.style_manager.register_style(DeyeWebConstants.item_table_style)
    style_id2 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)

    result = self.build_registers_str(registers)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <div id="{id}" class="tabcontent">
        <center>
          <table class="{style_id1}">
            {result}
          </table>
          {self.build_additional_data()}
          <br><br>
          <div class="counter {style_id2}">&nbsp;</div>
        </center>
      </div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()

  def build_register(self, title: str, register: DeyeRegister, on_click: str = '') -> str:
    for replace_from, replace_to in DeyeWebConstants.register_description_replacement_rules.items():
      title = title.replace(replace_from, replace_to)

    for reg, description in DeyeWebConstants.register_description_overriders.items():
      if register.name == reg.name:
        title = description
        break

    spacing = DeyeWebConstants.spacing_between_elements

    style_id1 = self.style_manager.register_style(
      f"font-size: {DeyeWebConstants.item_font_size}px; padding: {spacing}px; text-align: right;")
    style_id2 = self.style_manager.register_style(f"padding: {spacing}px;")

    if self.loggers.count > 1 and not self.only_master and register.avg_type != DeyeRegisterAverageType.only_master:
      details = ''
      for logger in self.loggers.loggers:
        details += f'{self.build_register_with_prefix(logger.name, register, on_click)}\n'

      prefix = self.loggers.accumulated_registers_prefix

      return f"""
        {DeyeWebUtils.begin_comment(self)}
        <tr>
          <td class="{style_id1}">
            {title.strip()}:
          </td>
          <td class="{style_id2}">
            <details>
              <summary>
                {self.build_register_with_prefix(prefix, register, on_click)}
              </summary>
                {details.strip()}
            </details>
          </td>
        </tr>
        {DeyeWebUtils.end_comment(self)}
      """.strip()
    else:
      prefix = self.loggers.master.name
      return f"""
        {DeyeWebUtils.begin_comment(self)}
        <tr>
          <td class="{style_id1}">
            {title}:
          </td>
          <td class="{style_id2}">
            {self.build_register_with_prefix(prefix, register, on_click)}
          </td>
        </tr>
        {DeyeWebUtils.end_comment(self)}
      """.strip()

  def build_register_with_prefix(self, prefix: str, register: DeyeRegister, on_click: str = '') -> str:
    id = DeyeWebUtils.short(f"{prefix}_{register.name}")
    on_click = f'onclick="{on_click}"' if on_click else ''
    cursor_style = DeyeWebConstants.cursor_style if on_click else ''
    cursor_style_id = f' {self.style_manager.register_style(cursor_style)}'.rstrip()

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <div {on_click} id="{id}" class="{DeyeWebConstants.remote_data_with_spinner_name}{cursor_style_id}" data-remote_field="{id}"></div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()

  def build_additional_data(self) -> str:
    return ''
