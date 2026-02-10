from typing import List

from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_register import DeyeRegister
from deye_web_section import DeyeWebSection
from deye_registers import DeyeRegisters
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_base_info_section import DeyeWebBaseInfoSection

class DeyeWebForecastSection(DeyeWebBaseInfoSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(DeyeWebSection.forecast)
    self._registers: List[DeyeRegister] = [
      registers.battery_soc_register,
      registers.battery_current_register,
      registers.battery_power_register,
    ]

  def build_additional_data(self) -> str:
    spacing = DeyeWebConstants.spacing_between_elements * 2

    id = DeyeWebUtils.short(self.section.title)
    style_id1 = self.style_manager.register_style(f"border-collapse: separate; border-spacing: {spacing}px;")

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <table class="{style_id1}">
        <tr>
          {self.build_command(DeyeWebRemoteCommand.get_forecast_by_percent, "By percent")}
          {self.build_command(DeyeWebRemoteCommand.get_forecast_by_time, "By time")}
        </tr>
      </table>
      <br>
      <div id="{id}" class="{DeyeWebConstants.remote_data_name} {DeyeWebConstants.temporary_data_name}" data-remote_field="{id}"></div>
      {DeyeWebUtils.end_comment(self)}
    """.strip()

  def build_command(self, command: DeyeWebRemoteCommand, name: str) -> str:
    id = DeyeWebUtils.short(self.section.title)
    style_id1 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
    style_id2 = self.style_manager.register_style(
      DeyeWebConstants.item_td_style_with_color.format(DeyeWebColor.green.color))
    cursor_style_id = self.style_manager.register_style(DeyeWebConstants.cursor_style)

    on_click = f"""onclick="{command.name}('{id}');" """

    return f"""
        <td {on_click} class="{style_id1} {style_id2} {cursor_style_id}">
          {name}
        </td>
      """
