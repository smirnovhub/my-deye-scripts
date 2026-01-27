import re

from typing import Any, Dict

from git_helper import GitHelper
from deye_utils import DeyeUtils
from deye_web_section import DeyeWebSection
from deye_web_utils import DeyeWebUtils
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from custom_single_registers import CustomSingleRegisters
from deye_web_color import DeyeWebColor
from deye_registers_holder import DeyeRegistersHolder
from deye_web_constants import DeyeWebConstants
from forecast_registers import ForecastRegisters
from battery_forecast_utils import BatteryForecastUtils
from battery_forecast_utils import BatteryForecastType
from deye_web_colors_calculator import DeyeWebColorsCalculator
from deye_web_formatters_config import DeyeWebFormattersConfig
from deye_web_remote_command import DeyeWebRemoteCommand
from deye_web_sections_holder import DeyeWebSectionsHolder
from deye_web_selections_config import DeyeWebSelectionsConfig
from deye_register_average_type import DeyeRegisterAverageType
from deye_web_selections_builder_config import DeyeWebSelectionsBuilderConfig
from deye_web_style_manager import DeyeWebStyleManager

class DeyeWebParamsProcessor:
  def __init__(self):
    self.loggers = DeyeWebConstants.loggers
    self.sections_holder = DeyeWebSectionsHolder()
    self.formatters_config = DeyeWebFormattersConfig()
    self.selections_config = DeyeWebSelectionsConfig()
    self.selections_builder_config = DeyeWebSelectionsBuilderConfig()
    self.style_manager = DeyeWebStyleManager()
    self.git_helper = GitHelper()

  def get_params(self, json_data: Any) -> Dict[str, str]:
    session_id = self.get_json_field(json_data, DeyeWebConstants.json_session_id_field)
    self.colors_calculator = DeyeWebColorsCalculator(self.sections_holder, session_id)

    command_value = self.get_json_field(json_data, DeyeWebConstants.json_command_field)

    try:
      command = DeyeWebRemoteCommand[command_value]
    except KeyError:
      raise ValueError(f"Invalid command: '{command_value}'")

    if command == DeyeWebRemoteCommand.read_registers:
      return self.read_registers()
    elif command == DeyeWebRemoteCommand.get_forecast_by_percent:
      return self.get_forecast(command)
    elif command == DeyeWebRemoteCommand.get_forecast_by_time:
      return self.get_forecast(command)
    elif command == DeyeWebRemoteCommand.update_scripts:
      return self.update_scripts()
    elif command == DeyeWebRemoteCommand.write_register:
      register_name = self.get_json_field(json_data, DeyeWebConstants.json_register_name_field)
      register_value = self.get_json_field(json_data, DeyeWebConstants.json_register_value_field)
      return self.write_register(register_name, register_value)
    else:
      raise ValueError(f"Invalid command: '{command}'")

  def get_json_field(self, json_data: Any, field_name: str) -> str:
    if field_name not in json_data:
      raise KeyError(f"Missing '{field_name}' field in JSON")

    value = json_data[field_name]

    if not isinstance(value, str):
      raise TypeError(f"Field '{field_name}' must be a string")

    return value

  def get_forecast(self, command: DeyeWebRemoteCommand) -> Dict[str, str]:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      name = 'deyeweb',
      socket_timeout = 5,
      register_creator = lambda prefix: ForecastRegisters(prefix),
    )

    try:
      holder.read_registers()
    finally:
      holder.disconnect()

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

      color = DeyeWebColor.green if forecast.type == BatteryForecastType.charge else DeyeWebColor.yellow

      spacing = DeyeWebConstants.spacing_between_elements

      style_id1 = self.style_manager.register_style(DeyeWebConstants.item_td_style)
      style_id2 = self.style_manager.register_style(DeyeWebConstants.item_td_style_with_color.format(color.color))
      style_id3 = self.style_manager.register_style(f"border-collapse: separate; border-spacing: {spacing}px;")

      result = ''

      result += f"""
          <table class="{style_id3}">
            <tr>
              <td colspan="3" class="{style_id1} {style_id2}">
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
              <td class="{style_id1} {style_id2}">{item.soc}%</td>
              <td class="{style_id1} {style_id2}">{date}</td>
              <td class="{style_id1} {style_id2}">{time}</td>
            </tr>
          """

      result += '</table>'

    result += self.style_manager.generate_css()

    id = DeyeWebUtils.short(DeyeWebSection.forecast.title)

    return {id: result}

  def update_scripts(self) -> Dict[str, str]:
    def get_result(result: str):
      id = DeyeWebUtils.short(DeyeWebSection.update.title)
      return {id: result + self.style_manager.generate_css()}

    try:
      current_branch_name = self.git_helper.get_current_branch_name()

      if current_branch_name == 'HEAD':
        return get_result('Unable to update: the repository is not currently on a branch')

      pull_result = self.git_helper.pull()

      if 'up to date' in pull_result.lower():
        last_commit = self.git_helper.get_last_commit_hash_and_comment()
        return get_result("Already up to date.<br>"
                          f"You are currently on '{current_branch_name}':<br><b>{last_commit}</b>")
    except Exception as e:
      err = str(e).replace(': ', ':<br>')
      return get_result(f'<p style="color: red;">{err}</p>')

    pattern = r'\d+ files? changed.*'
    matches = re.findall(pattern, pull_result)

    return get_result("\n".join(matches))

  def read_registers(self) -> Dict[str, str]:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      name = 'deyeweb',
      socket_timeout = 5,
    )

    try:
      holder.read_registers()
    finally:
      holder.disconnect()

    result: Dict[str, str] = {}
    colors: Dict[str, DeyeWebColor] = {}

    for inverter, registers in holder.all_registers.items():
      for register in registers.all_registers:
        if register.name not in self.sections_holder.used_registers:
          continue

        if register.avg_type == DeyeRegisterAverageType.only_master and inverter != self.loggers.master.name:
          continue

        if not register.can_accumulate and inverter == self.loggers.accumulated_registers_prefix:
          continue

        id = DeyeWebUtils.short(f'{inverter}_{register.name}')
        result[id] = DeyeWebUtils.clean(self.make_register_value(
          registers,
          register,
          colors,
        ))

    registers = holder.master_registers
    for register in registers.all_registers:
      if register.name not in self.sections_holder.used_registers:
        continue

      builder = self.selections_builder_config.get_selection_builder_for_register(register.name)
      selections = builder.build_selections(holder, register)
      result.update(selections)

    selection_colors = self.colors_calculator.get_sections_colors(colors)
    result.update(selection_colors)

    self.colors_calculator.save_colors(colors)

    result[DeyeWebConstants.result_read_styles_field] = self.style_manager.generate_css()

    return result

  def write_register(self, register_name: str, register_value: str) -> Dict[str, str]:
    if register_name not in self.sections_holder.writable_registers:
      raise ValueError(f"Can't write '{register_name}'")

    register = DeyeWebConstants.registers.get_register_by_name(register_name)
    if register is None:
      raise ValueError(f"Unknown register '{register_name}'")

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      name = 'deyeweb',
      socket_timeout = 5,
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(
        register,
        prefix,
      ),
    )

    try:
      holder.write_register(register, register_value)
    finally:
      holder.disconnect()

    result: Dict[str, str] = {}
    new_colors: Dict[str, DeyeWebColor] = {}

    colors = self.colors_calculator.load_colors()

    id = DeyeWebUtils.short(f'{self.loggers.master.name}_{register.name}')
    result[id] = DeyeWebUtils.clean(self.make_register_value(
      holder.master_registers,
      register,
      new_colors,
    ))

    builder = self.selections_builder_config.get_selection_builder_for_register(register.name)
    selections = builder.build_selections(holder, register)
    result.update(selections)

    for reg_name, color in new_colors.items():
      colors[reg_name] = color

    selection_colors = self.colors_calculator.get_sections_colors(colors)
    result.update(selection_colors)

    self.colors_calculator.save_colors(colors)

    result[DeyeWebConstants.result_write_styles_field] = self.style_manager.generate_css()

    return result

  def make_register_value(
    self,
    registers: DeyeRegisters,
    register: DeyeRegister,
    colors: Dict[str, DeyeWebColor],
  ) -> str:
    formatter = self.formatters_config.get_formatter_for_register(register.name)
    old_color = colors.get(register.name, DeyeWebColor.gray)
    new_color = formatter.get_color(registers, register)

    if register.avg_type == DeyeRegisterAverageType.only_master and registers.prefix != self.loggers.master.name:
      new_color = DeyeWebColor.gray

    if register.can_accumulate and registers.prefix != self.loggers.accumulated_registers_prefix:
      new_color = DeyeWebColor.gray

    if new_color.id > old_color.id and formatter.will_affect_tab_color:
      colors[register.name] = new_color

    return formatter.format_register(registers, register)
