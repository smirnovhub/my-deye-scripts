from typing import Any, Dict

from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_utils import DeyeUtils
from deye_web_color import DeyeWebColor
from battery_forecast_utils import BatteryForecastType
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_registers_holder import DeyeRegistersHolder
from deye_web_constants import DeyeWebConstants
from deye_web_forecast_registers import DeyeWebForecastRegisters
from battery_forecast_utils import BatteryForecastUtils
from processors.deye_web_base_command_processor import DeyeWebBaseCommandProcessor

class DeyeWebForecastCommandProcessor(DeyeWebBaseCommandProcessor):
  def __init__(self):
    super().__init__([
      DeyeWebRemoteCommand.get_forecast_by_percent,
      DeyeWebRemoteCommand.get_forecast_by_time,
    ])

  def get_command_result(
    self,
    command: DeyeWebRemoteCommand,
    json_data: Any,
  ) -> Dict[str, str]:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      name = 'deyeweb',
      loggers = self.loggers.loggers,
      socket_timeout = 5,
      auto_reconnect = True,
      register_creator = lambda prefix: DeyeWebForecastRegisters(prefix),
    )

    try:
      holder.read_registers()
    finally:
      holder.disconnect()

    spacing = DeyeWebConstants.spacing_between_elements

    id = DeyeWebUtils.short(DeyeWebSection.forecast.title)
    style_id1 = self.style_manager.register_style(
      DeyeWebConstants.item_td_style_with_color.format(DeyeWebColor.gray.color))
    style_id2 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
    style_id3 = self.style_manager.register_style(f"border-collapse: separate; border-spacing: {spacing}px;")

    try:
      if command == DeyeWebRemoteCommand.get_forecast_by_percent:
        forecast = BatteryForecastUtils.get_forecast_by_percent(
          battery_capacity = holder.master_registers.battery_capacity_register.value,
          battery_soc = holder.master_registers.battery_soc_register.value,
          battery_current = holder.accumulated_registers.battery_current_register.value,
        )
      else:
        forecast = BatteryForecastUtils.get_forecast_by_time(
          battery_capacity = holder.master_registers.battery_capacity_register.value,
          battery_soc = holder.master_registers.battery_soc_register.value,
          battery_current = holder.accumulated_registers.battery_current_register.value,
        )
    except Exception as e:
      result = f"""
          <table class="{style_id3}">
            <tr>
              <td class="{style_id1} {style_id2}">
                {str(e)}
              </td>
            </tr>
          </tdble>
        """
      return {id: result}

    color = DeyeWebColor.green if forecast.type == BatteryForecastType.charge else DeyeWebColor.yellow
    style_id4 = self.style_manager.register_style(DeyeWebConstants.item_td_style_with_color.format(color.color))

    result = ''

    result += f"""
        <table class="{style_id3}">
          <tr>
            <td colspan="3" class="{style_id2} {style_id4}">
      """

    if forecast.type == BatteryForecastType.charge:
      result += 'Charge forecast'
    else:
      result += 'Discharge forecast'

    result += """
          </td>
        </tr>
      """

    for item in forecast.items:
      soc_date_str = DeyeUtils.format_end_date(item.date)
      date, time = [item.strip() for item in soc_date_str.split(",")]
      result += f"""
          <tr>
            <td class="{style_id2} {style_id4}">{item.soc}%</td>
            <td class="{style_id2} {style_id4}">{date}</td>
            <td class="{style_id2} {style_id4}">{time}</td>
          </tr>
        """

    result += '</table>'
    result += self.style_manager.generate_css()

    return {id: result}
