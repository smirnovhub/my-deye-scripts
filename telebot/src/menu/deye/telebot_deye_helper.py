import telebot

from pprint import pprint
from typing import Dict, List, Union

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from empty_registers import EmptyRegisters
from telebot_auth_helper import TelebotAuthHelper
from deye_registers_holder import DeyeRegistersHolder
from deye_system_work_mode import DeyeSystemWorkMode
from deye_gen_port_mode import DeyeGenPortMode
from telebot_menu_item import TelebotMenuItem
from telebot_user_choices_helper import row_break_str

holder_kwargs = {
  'name': 'telebot',
  'socket_timeout': 7,
  'caching_time': 15,
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
  result = ""
  for register in registers:
    if isinstance(register.value, DeyeSystemWorkMode) or isinstance(register.value, DeyeGenPortMode):
      val = register.value.pretty
    else:
      val = str(register.value).title()

    desc = register.description.replace('Inverter ', '')
    desc = desc.replace('Grid Charging Start SOC', 'Max Charge SOC')
    result += f'{desc}: {val} {register.suffix}\n'

  return result

def write_register(register: DeyeRegister, value):
  """
  Write a value to the given Deye register.

  Connects to the inverter using a DeyeRegistersHolder, writes the value,
  and ensures the connection is closed afterwards.

  Parameters:
      register (DeyeRegister): The target register.
      value: The value to write.

  Returns:
      The value that was written.
  """
  loggers = DeyeLoggers()

  def creator(prefix):
    return EmptyRegisters(prefix)

  try:
    holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
    holder.connect_and_read()
    value = holder.write_register(register, value)
    return value
  finally:
    holder.disconnect()

def get_keyboard_for_register(
  registers: DeyeRegisters,
  register: DeyeRegister,
) -> Union[telebot.types.InlineKeyboardMarkup, None]:
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
  return None

def build_keyboard_for_register(
  register: DeyeRegister,
  rows: List[Union[List[str], Dict[str, str]]],
) -> telebot.types.InlineKeyboardMarkup:
  """
  Build an inline keyboard for a Telegram bot using a list of rows.
  
  Each row in `rows` can be either:
    1. List[str]: Each string in the list will be used as the button text.
        The callback_data for each button will be automatically generated
        as '{register.name}=<button_text>'.
    2. Dict[str, str]: Each key-value pair represents a button.
        The key is used as the button text, and the value is used as the
        callback_data.

  Parameters:
      register (DeyeRegister): The register object associated with this keyboard.
                                Its `name` attribute is used when generating
                                callback_data for List[str] rows.
      rows (List[Union[List[str], Dict[str, str]]]): The list of rows for the keyboard.
                                                    Each row can be a list of strings
                                                    or a dictionary mapping text -> callback.

  Returns:
      telebot.types.InlineKeyboardMarkup: The constructed inline keyboard object
                                          ready to be sent via the Telegram bot.

  Raises:
      TypeError: If any row in `rows` is not a list of strings or a dict of str->str.
  """
  # Initialize the InlineKeyboardMarkup object that will contain all rows
  keyboard = telebot.types.InlineKeyboardMarkup()

  # Iterate over each row in the provided rows
  for row in rows:
    buttons = [] # Temporary list to hold buttons for the current row

    if isinstance(row, list):
      # If the row is a list of strings, create buttons with text = label
      # and callback_data = "{register.name}={label}"
      buttons = [
        telebot.types.InlineKeyboardButton(text = label, callback_data = f'{register.name}={label}') for label in row
      ]

    elif isinstance(row, dict):
      # If the row is a dict, each key-value pair becomes a button
      # Key = button text, Value = callback_data
      buttons = [
        telebot.types.InlineKeyboardButton(text = text, callback_data = callback) for text, callback in row.items()
      ]

    else:
      # If row is neither list nor dict, raise a clear exception
      raise TypeError(f"build_keyboard_for_register(): row must be List[str] or Dict[str,str], got {type(row)}")

    # Add the buttons of the current row to the keyboard as a single row
    keyboard.row(*buttons)

  # Return the fully constructed keyboard object
  return keyboard

def get_choices_of_invertors(
  user_id: int,
  all_command: TelebotMenuItem,
  master_command: TelebotMenuItem,
  slave_command: TelebotMenuItem,
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
    choices[master_command.description] = f'/{master_command.command}'

  if auth_helper.is_menu_item_allowed(user_id, slave_command):
    for logger in loggers.loggers:
      if logger.name != loggers.master.name:
        command = slave_command.command.format(logger.name)
        description = slave_command.description.format(logger.name.title())
        choices[description] = f'/{command}'

  return choices

def get_available_registers(user_id: int) -> str:
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
  registers = DeyeRegisters()
  auth_helper = TelebotAuthHelper()

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
