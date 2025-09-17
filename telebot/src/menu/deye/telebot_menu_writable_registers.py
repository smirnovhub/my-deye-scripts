import telebot
import textwrap
import traceback

from typing import List
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from custom_registers import CustomRegisters
from deye_exceptions import DeyeKnownException
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from deye_registers_factory import DeyeRegistersFactory
from telebot_utils import remove_inline_buttons_with_delay

from telebot_constants import (
  buttons_remove_delay_sec,
  sync_inverter_time_str,
  inverter_system_time_need_sync_difference_sec,
)

from telebot_deye_helper import (
  write_register,
  build_keyboard_for_register,
  get_keyboard_for_register,
  holder_kwargs,
)

class TelebotMenuWritableRegisters(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot, is_authorized_func, is_writable_register_allowed_func):
    super().__init__(bot)
    self.is_authorized = is_authorized_func
    self.is_writable_register_allowed = is_writable_register_allowed_func
    self.registers = DeyeRegistersFactory.create_registers()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_writable_registers

  def get_commands(self) -> List[telebot.types.BotCommand]:
    commands = []
    for register in self.registers.read_write_registers:
      command_name = self.command.command.format(register.name)
      command_description = self.command.description.format(register.description)
      commands.append(telebot.types.BotCommand(command = command_name, description = command_description))
    return commands

  def register_handlers(self):
    for register in self.registers.read_write_registers:
      code = self.get_writable_register_handler(register)
      exec(code, locals())

  def check_callback_data(self, data: str) -> bool:
    parts = data.split('=', 1)
    if len(parts) != 2:
      return False

    register_name = parts[0]
    register = self.registers.get_register_by_name(register_name)
    return register is not None

  def get_writable_register_handler(self, register: DeyeRegister):
    @self.bot.callback_query_handler(func = lambda call: self.check_callback_data(call.data))
    def callback(call: telebot.types.CallbackQuery):
      self.bot.answer_callback_query(call.id)

      remove_inline_buttons_with_delay(
        bot = self.bot,
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        delay = buttons_remove_delay_sec,
      )

      # format should be: register_name=value
      parts = call.data.split('=', 1)
      register_name, value = parts
      register = self.registers.get_register_by_name(register_name)
      if register is None:
        self.bot.send_message(call.message.chat.id, f'Register {register_name} not found')
        self.bot.clear_step_handler_by_chat_id(call.message.chat.id)
        return

      if not self.is_writable_register_allowed(call.from_user.id, self.command, register.name):
        available_registers = self.get_available_registers(call.from_user.id)
        self.bot.send_message(
          call.message.chat.id,
          f'You can\'t change <b>{register.description}</b>. Available registers to change:\n{available_registers}',
          parse_mode = 'HTML')
        self.bot.clear_step_handler_by_chat_id(call.message.chat.id)
        return

      try:
        text = self.write_register(register, value)
        self.bot.send_message(call.message.chat.id, text, parse_mode = 'HTML')
      except DeyeKnownException as e:
        self.bot.send_message(call.message.chat.id, str(e))
      except Exception as e:
        self.bot.send_message(call.message.chat.id, str(e))
        print(traceback.format_exc())

      self.bot.clear_step_handler_by_chat_id(call.message.chat.id)

    return textwrap.dedent('''\
    @self.bot.message_handler(commands = ['{register_name}'])
    def set_{register_name}(message):
      self.process_read_write_register_step1(message, '{register_name}', set_{register_name}_step2)

    def set_{register_name}_step2(message, message_id: int):
      self.process_read_write_register_step2(message, message_id, '{register_name}')
  ''').format(register_name = register.name, register_description = register.description)

  def create_keyboard_for_register(self, register: DeyeRegister):
    if register.name == self.registers.inverter_system_time_register.name:
      time_diff = register.value - datetime.now()
      diff_seconds = int(abs(time_diff.total_seconds()))
      if diff_seconds > inverter_system_time_need_sync_difference_sec:
        return build_keyboard_for_register(register, [
          {
            sync_inverter_time_str: f'/{TelebotMenuItem.deye_sync_time.command}'
          },
        ])
      else:
        return None

    return get_keyboard_for_register(self.registers, register)

  def process_read_write_register_step1(self, message: telebot.types.Message, register_name: str, next_step_callback):
    if not self.is_authorized(message, self.command):
      return

    register = self.registers.get_register_by_name(register_name)
    if register is None:
      self.bot.send_message(message.chat.id, f'Register {register_name} not found')
      self.bot.clear_step_handler_by_chat_id(message.chat.id)
      return

    if not self.is_writable_register_allowed(message.from_user.id, self.command, register_name):
      available_registers = self.get_available_registers(message.from_user.id)
      self.bot.send_message(
        message.chat.id,
        f'You can\'t change <b>{register.description}</b>. Available registers to change:\n{available_registers}',
        parse_mode = 'HTML',
      )
      return

    try:
      text = self.get_register_value(register)
      keyboard = self.create_keyboard_for_register(register)
      sent = self.bot.send_message(message.chat.id, text, reply_markup = keyboard, parse_mode = 'HTML')
      self.bot.register_next_step_handler(message, next_step_callback, sent.message_id)
    except DeyeKnownException as e:
      self.bot.send_message(message.chat.id, str(e))
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      print(traceback.format_exc())

  def process_read_write_register_step2(self, message: telebot.types.Message, message_id: int, register_name: str):
    if not self.is_authorized(message, self.command):
      return

    # remove buttons from previous message
    remove_inline_buttons_with_delay(
      bot = self.bot,
      chat_id = message.chat.id,
      message_id = message_id,
      delay = buttons_remove_delay_sec,
    )

    # if we received new command, process it
    if message.text.startswith('/'):
      self.bot.process_new_messages([message])
      return

    register = self.registers.get_register_by_name(register_name)
    if register is None:
      self.bot.send_message(message.chat.id, f'Register {register_name} not found')
      self.bot.clear_step_handler_by_chat_id(message.chat.id)
      return

    if not message.text:
      self.bot.send_message(message.chat.id, f'Register value is empty')
      return

    try:
      text = self.write_register(register, message.text)
      self.bot.send_message(message.chat.id, text, parse_mode = 'HTML')
    except DeyeKnownException as e:
      self.bot.send_message(message.chat.id, str(e))
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      print(traceback.format_exc())

  def get_register_value(self, register: DeyeRegister):
    loggers = DeyeLoggers()

    def creator(prefix) -> DeyeRegisters:
      return CustomRegisters([register], prefix)

    try:
      holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
      holder.connect_and_read()
    finally:
      holder.disconnect()

    result = f'Current <b>{register.description}</b> value: {register.value} {register.suffix}\n'

    if register.min_value != register.max_value:
      result += f'Enter new value (from {register.min_value} to {register.max_value}):'
    else:
      result += f'Enter new value:'

    return result

  def write_register(self, register: DeyeRegister, text: str) -> str:
    if type(register.value) is int and register.value == int(text):
      return f'New value ({int(text)} {register.suffix}) is the same as old value. Nothing changed'

    if type(register.value) is float and register.value == float(text):
      return f'New value ({float(text)} {register.suffix}) is the same as old value. Nothing changed'

    value = write_register(register, text)
    return f'<b>{register.description}</b> changed to {value} {register.suffix}'

  def get_available_registers(self, user_id: int) -> str:
    str = ''
    num = 1
    for register in self.registers.read_write_registers:
      if self.is_writable_register_allowed(user_id, self.command, register.name):
        str += f'<b>{num}. {register.description}:</b>\n'
        str += f'/{register.name}\n'
        num += 1
    return str
