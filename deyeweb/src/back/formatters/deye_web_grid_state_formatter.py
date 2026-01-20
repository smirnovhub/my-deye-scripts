from deye_grid_state import DeyeGridState
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_utils import DeyeWebUtils
from deye_web_base_formatter import DeyeWebBaseFormatter

class DeyeWebGridStateFormatter(DeyeWebBaseFormatter):
  def format_register(self, registers: DeyeRegisters, register: DeyeRegister) -> str:
    value = self.get_formatted_value(register)
    grid_state = registers.grid_state_register.value
    color = DeyeWebColor.green if grid_state == DeyeGridState.on_grid else DeyeWebColor.red

    style_id1 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
    style_id2 = self.style_manager.register_style(DeyeWebConstants.item_td_style_with_color.format(color.color))

    cursor_style = self.get_cursor(registers, register)
    cursor_style_id = self.style_manager.register_style(cursor_style)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <table>
        <tr>
          <td class="{style_id1} {style_id2} {cursor_style_id}">
            {value}
          </td>
        </tr>
      </table>
      {DeyeWebUtils.end_comment(self)}
    """.strip()
