from typing import List, Optional

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_style_manager import DeyeWebStyleManager
from deye_web_graphs_config import DeyeWebGraphsConfig
from deye_web_value_formatter import DeyeWebValueFormatter

class DeyeWebBaseFormatter:
  def __init__(
    self,
    will_affect_tab_color: bool = True,
    used_registers: Optional[List[str]] = None,
  ):
    self.loggers = DeyeWebConstants.loggers
    self.graphs_config = DeyeWebGraphsConfig()
    self.style_manager = DeyeWebStyleManager()
    self.will_affect_tab_color = will_affect_tab_color
    self._used_registers: List[str] = used_registers if used_registers else []

  @property
  def used_registers(self) -> List[str]:
    return self._used_registers

  def get_formatted_value(self, register: DeyeRegister) -> str:
    if register.name in DeyeWebConstants.registers_without_formatting:
      return f'{register.pretty_value}{self.get_suffix(register.suffix)}'
    else:
      val = DeyeWebValueFormatter.get_formatted_value(register)
      return f'{val.value}{self.get_suffix(val.unit)}'.strip()

  def get_suffix(self, suffix: str) -> str:
    suffix = suffix.strip()

    for replace_from, replace_to in DeyeWebConstants.register_suffix_replacement_rules.items():
      suffix = suffix.replace(replace_from, replace_to)

    if len(suffix) > 1:
      return f'&nbsp;{suffix}'

    return suffix

  def get_color(self, registers: DeyeRegisters, register: DeyeRegister) -> DeyeWebColor:
    return DeyeWebColor.green

  def get_onclick(self, registers: DeyeRegisters, register: DeyeRegister) -> str:
    if registers.prefix == self.loggers.accumulated_registers_prefix:
      return ''

    url = self.graphs_config.get_url_for_register(register.name)
    return f"""onclick="openInNewTab('{url}');" """ if url else ''

  def get_cursor(self, registers: DeyeRegisters, register: DeyeRegister) -> str:
    if registers.prefix == self.loggers.accumulated_registers_prefix:
      return DeyeWebConstants.cursor_style

    url = self.graphs_config.get_url_for_register(register.name)
    return DeyeWebConstants.cursor_style if url else ''

  def format_register(self, registers: DeyeRegisters, register: DeyeRegister) -> str:
    value = self.get_formatted_value(register)
    color = self.get_color(registers, register)

    field_id = DeyeWebUtils.short(
      DeyeWebConstants.selection_content_field_template.format(registers.prefix, register.name))

    onclick = self.get_onclick(registers, register)

    style_id1 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
    style_id2 = self.style_manager.register_style(DeyeWebConstants.item_td_style_with_color.format(color.color))
    style_id3 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)

    cursor_style = self.get_cursor(registers, register)
    cursor_style_id = self.style_manager.register_style(cursor_style)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <table>
        <tr>
          <td {onclick} class="{style_id1} {style_id2} {cursor_style_id}">
            <div id="{field_id}" class="{style_id3}">
              {value}
            </div>
          </td>
        </tr>
      </table>
      {DeyeWebUtils.end_comment(self)}
    """.strip()
