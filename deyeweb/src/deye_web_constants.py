from typing import Dict, List

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_color import DeyeWebColor
from deye_web_section import DeyeWebSection

class DeyeWebConstants:
  default_open_tab = DeyeWebSection.info
  default_open_tab_id = 'default_open'
  tab_template = '{0}_tab'
  page_template = '{0}_page'
  tab_color_template = '{0}_color'
  selection_list_template = '{0}_{1}_list'
  selection_content_field_template = '{0}_{1}_content_field'
  remote_data_name = 'remote_data'
  remote_data_with_spinner_name = 'remote_data_with_spinner'
  temporary_data_name = 'temporary_data'

  grid_low_voltage_change_max_grid_power = 150

  item_font_size = 40
  item_width = 130
  item_height = 50
  item_padding = 18

  cursor_style = 'cursor: pointer;'

  flex_center_style = "display: flex; justify-content: center; align-items: center;"

  item_table_style = 'border-collapse: collapse; border-spacing: 0px; border: none;'

  item_td_style = (f'border: 1px solid black; min-width: {item_width}px; height: {item_height}px; '
                   f'text-align: center; padding: {item_padding}px; '
                   f'font-size: {item_font_size}px;')

  item_td_style_with_color = f'background-color: {{0}};'

  spacing_between_elements = 12

  json_session_id_field = 'session_id'
  json_command_field = 'command'
  json_register_name_field = 'register_name'
  json_register_value_field = 'register_value'
  result_error_field = 'error'
  result_callstack_field = 'callstack'
  result_read_styles_field = 'read_styles'
  result_write_styles_field = 'write_styles'

  add_html_comments = False
  user_short_html_ids = True
  clean_html_code = True
  print_call_stack_on_exception = False

  threshold_colors = [DeyeWebColor.green, DeyeWebColor.yellow, DeyeWebColor.red]
  threshold_reversed_colors = [DeyeWebColor.red, DeyeWebColor.yellow, DeyeWebColor.green]

  loggers = DeyeLoggers()
  registers = DeyeRegisters()

  register_description_replacement_rules: Dict[str, str] = {
    'Today': '',
    'Total': '',
    'Inverter': '',
    'External': '',
    'Energy': '',
    'Battery Max': 'Max',
    'Battery Grid': 'Grid',
    'Battery Gen': 'Gen',
    'Battery BMS': '',
    'Internal CT ': '',
  }

  register_suffix_replacement_rules: Dict[str, str] = {
    'sec': 's',
    'deg': '&deg;C',
  }

  register_description_overriders: Dict[DeyeRegister, str] = {
    registers.today_gen_energy_register: 'Gen Energy',
    registers.total_gen_energy_register: 'Gen Energy',
    registers.grid_connect_voltage_low_register: 'Grid Low Voltage',
  }

  registers_without_formatting: List[str] = [
    registers.grid_peak_shaving_power_register.name,
    registers.time_of_use_power_register.name,
  ]

  register_value_corrections: Dict[DeyeRegister, float] = {}
