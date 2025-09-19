import telebot
import traceback

from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_exceptions import DeyeKnownException
from custom_registers import CustomRegisters
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item import TelebotMenuItem
from deye_registers_holder import DeyeRegistersHolder
from deye_registers_factory import DeyeRegistersFactory
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import ask_confirmation

from telebot_constants import (
  inverter_system_time_does_not_need_sync_threshold_sec,
  inverter_system_time_too_big_difference_sec,
)

from telebot_deye_helper import (
  holder_kwargs,
  write_register,
  get_available_registers,
)

class TelebotMenuSyncTime(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.registers = DeyeRegistersFactory.create_registers()
    self.auth_helper = TelebotAuthHelper()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_sync_time

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message.from_user.id, message.chat.id):
      return

    register = self.registers.inverter_system_time_register

    if not self.auth_helper.is_writable_register_allowed(message.from_user.id, register.name):
      available_registers = get_available_registers(message.from_user.id)
      self.bot.send_message(
        message.chat.id,
        f'You can\'t change <b>{register.description}</b>. Available registers to change:\n{available_registers}',
        parse_mode = 'HTML')
      return

    def creator(prefix):
      return CustomRegisters([register], prefix)

    try:
      loggers = DeyeLoggers()
      holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
      holder.connect_and_read()
    except DeyeKnownException as e:
      self.bot.send_message(message.chat.id, f'Error while reading registers: {str(e)}')
    except Exception as e:
      self.bot.send_message(message.chat.id, f'Error while reading registers: {str(e)}')
      print(traceback.format_exc())
      return
    finally:
      holder.disconnect()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    time_diff = register.value - datetime.now()
    diff_seconds = int(abs(time_diff.total_seconds()))
    if diff_seconds > inverter_system_time_too_big_difference_sec:
      ask_confirmation(
        self.bot, message.chat.id, f'<b>Warning!</b> '
        f'Difference between inverter time and current time is too big:\n'
        f'Current time: <b>{now}</b>\n'
        f'Inverter time: <b>{register.value.strftime("%Y-%m-%d %H:%M:%S")}</b>\n'
        f'The difference is about {diff_seconds} seconds.\n'
        f'<b>Are you sure to sync inverter time?</b>', self.on_user_confirmation)
    elif diff_seconds > inverter_system_time_does_not_need_sync_threshold_sec:
      self.on_user_confirmation(message.chat.id, True)
    else:
      self.bot.send_message(message.chat.id, 'The inverter time is already synced', parse_mode = 'HTML')

  def on_user_confirmation(self, chat_id: int, result: bool):
    if result:
      try:
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        register = self.registers.inverter_system_time_register
        text = self.process_read_write_register_step2(register, value)
        self.bot.send_message(chat_id, text, parse_mode = 'HTML')
      except DeyeKnownException as e:
        self.bot.send_message(chat_id, f'Error while writing registers: {str(e)}')
      except Exception as e:
        self.bot.send_message(chat_id, f'Error while writing registers: {str(e)}')
        print(traceback.format_exc())
    else:
      self.bot.send_message(chat_id, 'Time sync cancelled')

  def process_read_write_register_step2(self, register: DeyeRegister, text: str) -> str:
    if type(register.value) is int and register.value == int(text):
      return f'New value ({int(text)}) is the same as old value ({register.value}). Do nothing'

    if type(register.value) is float and register.value == float(text):
      return f'New value ({float(text)}) is the same as old value ({register.value}). Do nothing'

    value = write_register(register, text)
    return f'<b>{register.description}</b> changed to {value} {register.suffix}'
