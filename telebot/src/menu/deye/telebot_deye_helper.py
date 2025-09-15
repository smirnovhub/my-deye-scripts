from typing import List, Union
from telebot_constants import *
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from empty_registers import EmptyRegisters
from deye_registers_holder import DeyeRegistersHolder
from deye_system_work_mode import DeyeSystemWorkMode
from deye_gen_port_mode import DeyeGenPortMode
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

holder_kwargs = {
  'name': 'telebot',
  'socket_timeout': 7,
  'caching_time': 15,
#  'verbose': True,
}

def get_register_values(registers: List[DeyeRegister]) -> str:
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
  loggers = DeyeLoggers()

  def creator(prefix):
    return EmptyRegisters(prefix)

  try:
    holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
    holder.connect_and_read()
    value = holder.write_register(register, value)
    return value
  except Exception as e:
    raise Exception(str(e))
  finally:
    holder.disconnect()

def get_keyboard_for_register(registers: DeyeRegisters, register: DeyeRegister) -> Union[InlineKeyboardMarkup, None]:
  if register.name == registers.ac_couple_frz_high_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['50.5', '51', '51.5', '52'],
      ])
  elif register.name == registers.backup_delay_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['0', '100', '250', '500'],
        ['1000', '2000', '3000', '5000'],
        ['7000', '10000', '15000', '30000'],
      ])
  elif register.name == registers.battery_gen_charge_current_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['0', '1', '3', '5', '7'],
        ['10', '15', '20', '25', '30'],
        ['35', '40', '45', '50', '55'],
        ['60', '65', '70', '75', '80'],
      ])
  elif register.name == registers.battery_grid_charge_current_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['0', '1', '3', '5', '7'],
        ['10', '15', '20', '25', '30'],
        ['35', '40', '45', '50', '55'],
        ['60', '65', '70', '75', '80'],
      ])
  elif register.name == registers.battery_low_batt_soc_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['5', '10', '15', '20', '25'],
        ['30', '35', '40', '45', '50'],
      ])
  elif register.name == registers.battery_max_charge_current_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['0', '1', '3', '5', '7'],
        ['10', '15', '20', '25', '30'],
        ['35', '40', '45', '50', '55'],
        ['60', '65', '70', '75', '80'],
      ])
  elif register.name == registers.battery_restart_soc_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['5', '10', '15', '20', '25'],
        ['30', '35', '40', '45', '50'],
      ])
  elif register.name == registers.battery_shutdown_soc_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['5', '10', '15', '20', '25'],
        ['30', '35', '40', '45', '50'],
      ])
  elif register.name == registers.grid_charging_start_soc_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['50', '55', '60'],
        ['65', '70', '75'],
        ['80', '85', '90'],
      ])
  elif register.name == registers.grid_reconnection_time_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['60', '120', '240'],
        ['300', '420', '480'],
        ['600', '720', '900'],
      ])
  elif register.name == registers.grid_peak_shaving_power_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['1000', '1500', '2000'],
        ['2500', '3000', '3500'],
        ['4000', '4500', '5000'],
      ])
  elif register.name == registers.gen_peak_shaving_power_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['1000', '1500', '2000'],
        ['2500', '3000', '3500'],
        ['4000', '4500', '5000'],
      ])
  elif register.name == registers.time_of_use_power_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['0', '250', '500'],
        ['1000', '1500', '2000'],
        ['2500', '3000', '3500'],
        ['4000', '5000', '6000'],
      ])
  elif register.name == registers.time_of_use_soc_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['15', '20', '25', '30', '35'],
        ['40', '45', '50', '55', '60'],
        ['65', '70', '75', '80', '85'],
        ['90', '95', '100'],
      ])
  elif register.name == registers.zero_export_power_register.name:
    return build_keyboard_for_register(
      register,
      [
        ['0', '5', '10', '15'],
        ['20', '25', '30', '35'],
        ['40', '45', '50', '60'],
        ['70', '80', '90', '100'],
      ])
  elif register.name == registers.inverter_system_time_register.name:
    return build_keyboard_for_register(
      register,
      [
        [sync_inverter_time_str],
      ])
  return None

# Creates an inline keyboard for the Telegram bot.
# :param rows: list of lists of strings
#               (each nested list = one row of buttons)
# :return: InlineKeyboardMarkup
def build_keyboard_for_register(register: DeyeRegister, rows: List[List[str]]) -> InlineKeyboardMarkup:
  keyboard = InlineKeyboardMarkup()
  for row in rows:
    # Create one row of buttons
    buttons = [InlineKeyboardButton(text = label, callback_data = f'{register.name}={label}') for label in row]
    keyboard.row(*buttons)
  return keyboard
