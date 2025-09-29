import telebot

from pprint import pprint
from typing import Dict, List, Optional, Union

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from telebot_auth_helper import TelebotAuthHelper
from deye_base_enum import DeyeBaseEnum
from telebot_menu_item import TelebotMenuItem
from telebot_user_choices_helper import row_break_str

holder_kwargs = {
  'name': 'telebot',
  'socket_timeout': 10,
  'caching_time': 5,
  #  'verbose': True,
}

def get_register_values(registers: List[DeyeRegister]) -> str:
  """
  Generate a formatted string with the values of the given Deye registers.

  For each register, formats the value (using `.pretty` if applicable) 
  and appends its description and suffix.

  Parameters:
      registers (List[DeyeRegister]): List of registers to process.

  Returns:
      str: A multi-line string with each register's description and value.
  """
  result = ''

  for register in registers:
    desc = register.description.replace('Inverter ', '')
    result += f'{desc}: {register.pretty_value} {register.suffix}\n'

  return result

def get_keyboard_for_register(
  registers: DeyeRegisters,
  register: DeyeRegister,
) -> Optional[telebot.types.InlineKeyboardMarkup]:
  """
  Return a pre-defined inline keyboard for the given register.

  Selects the appropriate set of buttons based on the register's name 
  and builds a Telegram inline keyboard. Returns None if no keyboard 
  is defined for the register.

  Parameters:
      registers (DeyeRegisters): The collection of all registers.
      register (DeyeRegister): The specific register to create a keyboard for.

  Returns:
      telebot.types.InlineKeyboardMarkup | None: Inline keyboard or None.
  """
  if register.name == registers.ac_couple_frz_high_register.name:
    return build_keyboard_for_register(register, [
      ['50.5', '51', '51.5', '52'],
    ])
  elif register.name == registers.backup_delay_register.name:
    return build_keyboard_for_register(register, [
      ['0', '100', '250', '500'],
      ['1000', '2000', '3000', '5000'],
      ['7000', '10000', '15000', '30000'],
    ])
  elif register.name == registers.battery_gen_charge_current_register.name:
    return build_keyboard_for_register(register, [
      ['0', '1', '3', '5', '7'],
      ['10', '15', '20', '25', '30'],
      ['35', '40', '45', '50', '55'],
      ['60', '65', '70', '75', '80'],
    ])
  elif register.name == registers.battery_grid_charge_current_register.name:
    return build_keyboard_for_register(register, [
      ['0', '1', '3', '5', '7'],
      ['10', '15', '20', '25', '30'],
      ['35', '40', '45', '50', '55'],
      ['60', '65', '70', '75', '80'],
    ])
  elif register.name == registers.battery_low_batt_soc_register.name:
    return build_keyboard_for_register(register, [
      ['5', '10', '15', '20', '25'],
      ['30', '35', '40', '45', '50'],
    ])
  elif register.name == registers.battery_max_charge_current_register.name:
    return build_keyboard_for_register(register, [
      ['0', '1', '3', '5', '7'],
      ['10', '15', '20', '25', '30'],
      ['35', '40', '45', '50', '55'],
      ['60', '65', '70', '75', '80'],
    ])
  elif register.name == registers.battery_restart_soc_register.name:
    return build_keyboard_for_register(register, [
      ['5', '10', '15', '20', '25'],
      ['30', '35', '40', '45', '50'],
    ])
  elif register.name == registers.battery_shutdown_soc_register.name:
    return build_keyboard_for_register(register, [
      ['5', '10', '15', '20', '25'],
      ['30', '35', '40', '45', '50'],
    ])
  elif register.name == registers.grid_charging_start_soc_register.name:
    return build_keyboard_for_register(register, [
      ['50', '55', '60'],
      ['65', '70', '75'],
      ['80', '85', '90'],
    ])
  elif register.name == registers.grid_reconnection_time_register.name:
    return build_keyboard_for_register(register, [
      ['60', '120', '240'],
      ['300', '420', '480'],
      ['600', '720', '900'],
    ])
  elif register.name == registers.grid_peak_shaving_power_register.name:
    return build_keyboard_for_register(register, [
      ['1000', '1500', '2000'],
      ['2500', '3000', '3500'],
      ['4000', '4500', '5000'],
    ])
  elif register.name == registers.gen_peak_shaving_power_register.name:
    return build_keyboard_for_register(register, [
      ['1000', '1500', '2000'],
      ['2500', '3000', '3500'],
      ['4000', '4500', '5000'],
    ])
  elif register.name == registers.time_of_use_power_register.name:
    return build_keyboard_for_register(register, [
      ['0', '250', '500'],
      ['1000', '1500', '2000'],
      ['2500', '3000', '3500'],
      ['4000', '5000', '6000'],
    ])
  elif register.name == registers.time_of_use_soc_register.name:
    return build_keyboard_for_register(register, [
      ['15', '20', '25', '30', '35'],
      ['40', '45', '50', '55', '60'],
      ['65', '70', '75', '80', '85'],
      ['90', '93', '95', '97', '100'],
    ])
  elif register.name == registers.zero_export_power_register.name:
    return build_keyboard_for_register(register, [
      ['0', '5', '10', '15'],
      ['20', '25', '30', '35'],
      ['40', '45', '50', '60'],
      ['70', '80', '90', '100'],
    ])
  elif isinstance(register.value, DeyeBaseEnum):
    buttons_dict: Dict[str, str] = {}
    for enum_item in type(register.value):
      if enum_item.value >= 0:
        buttons_dict[enum_item.pretty] = f'/{register.name} {enum_item}'
        buttons_dict[str(enum_item.value)] = row_break_str
    return build_keyboard_for_register(register, [buttons_dict])
  return None

def build_keyboard_for_register(
  register: DeyeRegister,
  rows: List[Union[List[str], Dict[str, str]]],
) -> telebot.types.InlineKeyboardMarkup:
  """
  Build a Telegram InlineKeyboardMarkup for a given Deye register.

  This function generates an inline keyboard where each row corresponds
  to a list or dictionary of values provided in `rows`. It supports dynamic
  creation of rows, and can insert line breaks when a special value is encountered.

  Behavior:
  - If a row is a list of strings, each string becomes a button with:
      - `text` = the string value
      - `callback_data` = "/<register.name> <value>"
  - If a row is a dictionary, each key-value pair becomes a button with:
      - `text` = key
      - `callback_data` = value
  - If the special string row_break_str appears in a list, or as a key or value in a dictionary,
    a line break is inserted:
      - All buttons accumulated so far are added as a row
      - The row_break_str itself is skipped
  - Both lists and dictionaries can be mixed across rows
  - Any row that is not a `list` or `dict` will raise a `TypeError`

  Args:
      register (DeyeRegister): The register for which the keyboard is built.
          Its `name` attribute is used to construct callback data for list entries.
      rows (List[Union[List[str], Dict[str, str]]]): A list of rows, where each row is either:
          - A list of strings representing button labels, or
          - A dictionary mapping button labels (keys) to callback data (values).

  Returns:
      telebot.types.InlineKeyboardMarkup: The constructed inline keyboard ready to be sent
      with a Telegram message.

  Raises:
      TypeError: If a row is not a list or dictionary.
  """
  # Initialize the InlineKeyboardMarkup object that will contain all rows
  keyboard = telebot.types.InlineKeyboardMarkup()

  # Iterate over each row in the provided rows
  for row in rows:
    buttons: List[telebot.types.InlineKeyboardButton] = []

    if isinstance(row, list):
      # If the row is a list of strings, create buttons with text = label
      # and callback_data = "/{register.name} {value}"
      for value in row:
        if value == row_break_str:
          if buttons:
            keyboard.row(*buttons)
            buttons = []
          continue
        buttons.append(telebot.types.InlineKeyboardButton(text = value, callback_data = f'/{register.name} {value}'))

    elif isinstance(row, dict):
      # If the row is a dict, each key-value pair becomes a button
      # Key = button text, Value = callback_data
      for text, callback in row.items():
        if row_break_str in (text, callback):
          if buttons:
            keyboard.row(*buttons)
            buttons = []
          continue
        buttons.append(telebot.types.InlineKeyboardButton(text = text, callback_data = callback))

    else:
      # If row is neither list nor dict, raise a clear exception
      raise TypeError(f"build_keyboard_for_register(): row must be List[str] or Dict[str,str], got {type(row)}")

    # Add remaining buttons for the current row
    if buttons:
      keyboard.row(*buttons)

  # Return the fully constructed keyboard object
  return keyboard

def get_choices_of_inverters(
  user_id: int,
  all_command: TelebotMenuItem,
  master_command: TelebotMenuItem,
  slave_command: Optional[TelebotMenuItem],
) -> Dict[str, str]:
  """
  Generate a dictionary of inline button choices for inverters.

  Includes entries for "all", master, and slave inverters.
  Keys are button labels (descriptions), values are callback commands.

  Parameters:
      all_command (TelebotMenuItem): Command for all inverters.
      master_command (TelebotMenuItem): Command for the master inverter.
      slave_command (TelebotMenuItem): Command template for slave inverters.

  Returns:
      Dict[str, str]: Mapping of button text to callback command.
  """
  loggers = DeyeLoggers()
  auth_helper = TelebotAuthHelper()

  choices: Dict[str, str] = {}
  if loggers.count == 1:
    return choices

  if auth_helper.is_menu_item_allowed(user_id, all_command):
    choices[all_command.description] = f'/{all_command.command}'
    # add line break
    choices[row_break_str] = row_break_str

  if auth_helper.is_menu_item_allowed(user_id, master_command):
    master_name = loggers.master.name
    command = master_command.command.format(master_name)
    description = master_command.description.format(master_name.title())
    choices[description] = f'/{command}'

  if slave_command is None:
    return choices

  if auth_helper.is_menu_item_allowed(user_id, slave_command):
    for logger in loggers.loggers:
      if logger.name != loggers.master.name:
        command = slave_command.command.format(logger.name)
        description = slave_command.description.format(logger.name.title())
        choices[description] = f'/{command}'

  return choices

def get_available_registers(registers: DeyeRegisters, auth_helper: TelebotAuthHelper, user_id: int) -> str:
  """
  Return a formatted string listing all writable registers available to a user.

  Iterates over all read/write registers and includes only those
  that the user is allowed to write to.
  Each register is numbered and includes its description and command name.

  Args:
      user_id (int): Telegram user ID to check permissions for

  Returns:
      str: Formatted string with available registers for the user
  """
  str = ''
  num = 1
  for register in registers.read_write_registers:
    if auth_helper.is_writable_register_allowed(user_id, register.name):
      str += f'<b>{num}. {register.description}:</b>\n'
      str += f'/{register.name}\n'
      num += 1
  return str

def debug_print(obj):
  """Pretty-print any Python object directly using pprint."""
  def to_serializable(o):
    if isinstance(o, list):
      # Recursively handle lists
      return [to_serializable(item) for item in o]
    elif isinstance(o, dict):
      # Recursively handle dicts
      return {k: to_serializable(v) for k, v in o.items()}
    elif hasattr(o, "__dict__"):
      # Convert custom object attributes to dict
      return {k: to_serializable(v) for k, v in o.__dict__.items()}
    else:
      # Base types (int, str, bool, etc.)
      return o

  pprint(to_serializable(obj))
