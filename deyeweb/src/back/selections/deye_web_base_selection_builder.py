from typing import Dict, List

from deye_register import DeyeRegister
from deye_web_utils import DeyeWebUtils
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_style_manager import DeyeWebStyleManager
from deye_web_formatters_config import DeyeWebFormattersConfig
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_selections_config import DeyeWebSelectionsConfig
from deye_registers_holder import DeyeRegistersHolder

class DeyeWebBaseSelectionBuilder:
  def __init__(self):
    self.loggers = DeyeWebConstants.loggers
    self.selections_config = DeyeWebSelectionsConfig()
    self.formatters_config = DeyeWebFormattersConfig()
    self.style_manager = DeyeWebStyleManager()

  def build_selections(self, holder: DeyeRegistersHolder, register: DeyeRegister) -> Dict[str, str]:
    selections = self.selections_config.get_selections_for_register(register.name)
    if not selections:
      return {}

    result = DeyeWebUtils.clean(self.build_selections_html(holder, register, selections))

    id = DeyeWebUtils.short(
      f'{DeyeWebConstants.selection_list_template.format(self.loggers.master.name, register.name)}')

    return {id: result}

  def build_selections_html(
    self,
    holder: DeyeRegistersHolder,
    register: DeyeRegister,
    selections: List[float],
    disabled: bool = False,
  ) -> str:
    formatter = self.formatters_config.get_formatter_for_register(register.name)

    row_count = 3
    spacing = DeyeWebConstants.spacing_between_elements * 2

    style_id0 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)
    style_id1 = self.style_manager.register_style(f"border-collapse: separate; border-spacing: {spacing}px;")
    style_id2 = self.style_manager.register_style("text-align: center;")
    style_id3 = self.style_manager.register_style("display: inline-table; width: auto; margin: 0;")

    result = f"""
      {DeyeWebUtils.begin_comment(self)}
      <div class="{style_id0}">
      <table class="{style_id1}">
        <tr>
          <td colspan="{row_count}" class="{style_id2}">
            <table class="{style_id3}">
              <tr>
                <td>
                  {formatter.format_register(holder.master_registers, register)}
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
      """.strip()

    def equal(val1: float, val2: float) -> bool:
      return abs(val1 - val2) < 0.0001

    cnt = 0
    correction: float = 0

    for reg, corr in DeyeWebConstants.register_value_corrections.items():
      if reg.name == register.name:
        correction = corr

    registers = holder.master_registers
    value = register.value + correction
    suffix = formatter.get_suffix(register.suffix)
    color = formatter.get_color(registers, register)

    for val in selections:
      val_color = color if equal(value, val) else DeyeWebColor.gray
      register_field_id = DeyeWebUtils.short(
        DeyeWebConstants.selection_content_field_template.format(registers.prefix, register.name))
      field_id = DeyeWebUtils.short(f'{register.name}_{cnt}')
      command = DeyeWebRemoteCommand.write_register.name

      on_click = ''
      if not disabled and not equal(value, val):
        on_click = f"""onclick="{command}('{register_field_id}', '{field_id}', '{register.name}', '{val - correction}')" """

      style_id4 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
      style_id5 = self.style_manager.register_style(DeyeWebConstants.item_td_style_with_color.format(val_color.color))
      style_id6 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)
      style_id7 = self.style_manager.register_style("position: relative; display: inline-block;")

      cursor_style = "" if disabled or equal(value, val) else DeyeWebConstants.cursor_style
      cursor_style_id = self.style_manager.register_style(cursor_style)

      if disabled:
        result += f"""
          <td {on_click} class="{style_id4} {style_id5} {cursor_style_id}">
            <div id="{field_id}" class="{style_id6} {style_id7}">
              {val}{suffix}
              <div class="dark-overlay"></div>
              <img src="images/lock.svg" class="lock-overlay">
            </div>
          </td>
        """
      else:
        result += f"""
          <td {on_click} class="{style_id4} {style_id5} {cursor_style_id}">
            <div id="{field_id}" class="{style_id6}">
              {val}{suffix}
            </div>
          </td>
        """

      cnt += 1

      if cnt < len(selections) and (cnt % row_count) == 0:
        result += "</tr>\n<tr>\n"

    result += f"""
        </tr>
        </table>
        </div>
        {DeyeWebUtils.end_comment(self)}
      """.strip()

    return result
