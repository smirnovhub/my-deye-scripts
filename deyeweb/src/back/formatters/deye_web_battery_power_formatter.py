from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_constants import DeyeWebConstants
from deye_web_utils import DeyeWebUtils
from deye_web_threshold_formatter import DeyeWebThresholdFormatter

class DeyeWebBatteryPowerFormatter(DeyeWebThresholdFormatter):
  def __init__(
    self,
    threshold1: float,
    threshold2: float,
  ):
    super().__init__(
      threshold1,
      threshold2,
      DeyeWebConstants.threshold_reversed_colors,
    )

  def get_color(self, registers: DeyeRegisters, register: DeyeRegister) -> DeyeWebColor:
    threshold = self.threshold1

    if registers.prefix == self.loggers.accumulated_registers_prefix:
      threshold *= self.loggers.count

    if abs(register.value) >= threshold:
      return DeyeWebColor.red

    return super().get_color(registers, register)

  def format_register(self, registers: DeyeRegisters, register: DeyeRegister) -> str:
    value = self.get_formatted_value(register)

    battery_power = registers.battery_power_register.value
    battery_current = registers.battery_current_register.value
    max_battery_power = registers._time_of_use_power_register.value
    max_battery_charge_current = registers.battery_max_charge_current_register.value
    max_battery_discharge_current = registers.battery_max_discharge_current_register.value

    threshold = self.threshold1

    if registers.prefix == self.loggers.accumulated_registers_prefix:
      threshold *= self.loggers.count

    if abs(register.value) >= threshold:
      percent = round(battery_current * 100 / max_battery_discharge_current)
      color1 = DeyeWebColor.red
      color2 = DeyeWebColor.light_red
    elif battery_current > 0:
      percent = round(battery_power * 100 / max_battery_power)
      color1 = DeyeWebColor.yellow
      color2 = DeyeWebColor.light_yellow
    elif battery_current < 0:
      if abs(max_battery_charge_current) < 0.01:
        percent = 100
      else:
        percent = -round(battery_current * 100 / max_battery_charge_current)

      color1 = DeyeWebColor.green
      color2 = DeyeWebColor.light_green
    else:
      percent = 0
      color1 = DeyeWebColor.green
      color2 = DeyeWebColor.light_green

    # clamp to 0–100
    percent = max(0, min(100, percent))

    mode_text = "(idle)"
    if battery_power > 0:
      mode_text = "(discharging)"
    elif battery_power < 0:
      mode_text = "(charging)"

    width = round(DeyeWebConstants.item_width * 1.3)
    padding = DeyeWebConstants.item_padding

    onclick = self.get_onclick(registers, register)

    style1 = f"""
        min-width: {width}px;
        text-align: center;
        padding-left: {padding}px;
        padding-right: {padding}px;
      """

    style2 = f"""
        background: linear-gradient(to right, {color1.color} {percent}%, {color2.color} {percent}%);
      """

    style3 = f"""
        height: {DeyeWebConstants.item_height}px;
        font-size: {DeyeWebConstants.item_font_size}px;
        padding-top: 7px;
      """

    style4 = f"""
        height: {round(DeyeWebConstants.item_height / 2)}px;
        font-size: {round(DeyeWebConstants.item_font_size / 2)}px;
        padding-bottom: 15px;
      """

    style_id1 = self.style_manager.register_style(style1)
    style_id2 = self.style_manager.register_style(style2)
    style_id3 = self.style_manager.register_style(style3)
    style_id4 = self.style_manager.register_style(style4)

    table_style_id = self.style_manager.register_style("border: 1px solid black;")
    cursor_style_id = self.style_manager.register_style(DeyeWebConstants.cursor_style)

    return f"""
      {DeyeWebUtils.begin_comment(self)}
      <table class="{table_style_id}">
        <tr>
          <td {onclick} class="{style_id1} {style_id2} {style_id3} {cursor_style_id}">
            {value}
          </td>
        </tr>
        <tr>
          <td {onclick} class="{style_id1} {style_id2} {style_id4} {cursor_style_id}">
            {mode_text}
          </td>
        </tr>
      </table>
      {DeyeWebUtils.end_comment(self)}
    """.strip()
