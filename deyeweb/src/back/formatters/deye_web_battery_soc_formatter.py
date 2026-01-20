from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_utils import DeyeWebUtils
from deye_web_threshold_formatter import DeyeWebThresholdFormatter

class DeyeWebBatterySocFormatter(DeyeWebThresholdFormatter):
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

  def format_register(self, registers: DeyeRegisters, register: DeyeRegister) -> str:
    if not isinstance(register.value, int):
      return super().format_register(registers, register)

    color1 = super().get_color(registers, register)
    color2 = color1

    if color1 == DeyeWebColor.green:
      color2 = DeyeWebColor.light_green
    elif color1 == DeyeWebColor.yellow:
      color2 = DeyeWebColor.light_yellow
    elif color1 == DeyeWebColor.red:
      color2 = DeyeWebColor.light_red

    percent = register.value

    # clamp to 0–100
    percent = max(0, min(100, percent))
    value = self.get_formatted_value(register)
    onclick = self.get_onclick(registers, register)

    style = f"""
        background: linear-gradient(to right,
        {color1.color} {percent}%, {color2.color} {percent}%);
      """

    style_id1 = self.style_manager.register_style(style)
    style_id2 = self.style_manager.register_style(DeyeWebConstants.item_td_style)

    cursor_style = self.get_cursor(registers, register)
    cursor_style_id = self.style_manager.register_style(cursor_style)

    return f"""
        {DeyeWebUtils.begin_comment(self)}
        <table>
          <tr>
            <td {onclick} class="{style_id1} {style_id2} {cursor_style_id}">
              {value}
            </td>
          </tr>
        </table>
        {DeyeWebUtils.end_comment(self)}
      """.strip()
