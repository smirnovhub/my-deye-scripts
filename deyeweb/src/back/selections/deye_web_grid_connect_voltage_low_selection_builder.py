from typing import List

from deye_register import DeyeRegister
from deye_registers_holder import DeyeRegistersHolder
from deye_web_constants import DeyeWebConstants
from deye_grid_state import DeyeGridState
from deye_web_base_selection_builder import DeyeWebBaseSelectionBuilder

class DeyeWebGridConnectVoltageLowSelectionBuilder(DeyeWebBaseSelectionBuilder):
  def __init__(self):
    super().__init__(confirm = True)

  def build_selections_html(
    self,
    holder: DeyeRegistersHolder,
    register: DeyeRegister,
    selections: List[float],
    disabled: bool = False,
  ) -> str:
    is_power_too_high = self.is_grid_power_too_high(holder)
    result = super().build_selections_html(
      holder,
      register,
      selections,
      disabled = is_power_too_high,
    )

    style_id1 = self.style_manager.register_style(DeyeWebConstants.flex_center_style)
    style_id2 = self.style_manager.register_style("text-align: center; font-size: 30px; color: red;")

    warning = ''
    if is_power_too_high:
      warning = f"""
        <div class="{style_id1}">
            <table>
              <tr>
                <td class="{style_id2}">
                  Can't change!<br>
                  Grid power is too high!
                </td>
              </tr>
            </table>
        </div>
        <br>
      """

    return f"""
        {result}
        {warning}
      """

  def is_grid_power_too_high(self, holder: DeyeRegistersHolder) -> bool:
    if holder.accumulated_registers.grid_state_register.value == DeyeGridState.off_grid:
      return False

    grid_power = abs(holder.accumulated_registers.grid_power_register.value)
    return grid_power > DeyeWebConstants.grid_low_voltage_change_max_grid_power
