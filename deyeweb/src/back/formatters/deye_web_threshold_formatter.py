from typing import Any, List

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_utils import DeyeWebUtils
from deye_register_average_type import DeyeRegisterAverageType
from deye_web_constants import DeyeWebConstants
from deye_web_base_formatter import DeyeWebBaseFormatter

class DeyeWebThresholdFormatter(DeyeWebBaseFormatter):
  def __init__(
    self,
    threshold1: float,
    threshold2: float,
    colors: List[DeyeWebColor],
    will_affect_tab_color: bool = True,
  ):
    super().__init__(will_affect_tab_color)
    self.threshold1 = threshold1
    self.threshold2 = threshold2
    self.colors = colors

  def get_register_value(self, register: DeyeRegister) -> Any:
    return register.value

  def get_color(self, registers: DeyeRegisters, register: DeyeRegister) -> DeyeWebColor:
    threshold1 = self.threshold1
    threshold2 = self.threshold2

    if register.avg_type == DeyeRegisterAverageType.only_master and registers.prefix != self.loggers.master.name:
      return DeyeWebColor.green

    if register.avg_type == DeyeRegisterAverageType.accumulate and registers.prefix == self.loggers.accumulated_registers_prefix:
      threshold1 *= self.loggers.count
      threshold2 *= self.loggers.count

    value = self.get_register_value(register)

    if value >= threshold1:
      return self.colors[0]
    elif value >= threshold2:
      return self.colors[1]
    else:
      return self.colors[2]

  def format_register(self, registers: DeyeRegisters, register: DeyeRegister) -> str:
    if not isinstance(register.value, float) and not isinstance(register.value, int):
      return super().format_register(registers, register)

    color = self.get_color(registers, register)
    value = self.get_formatted_value(register)

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
