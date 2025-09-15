import textwrap
import telebot

from typing import cast
from datetime import datetime, timedelta, timezone

from telebot_constants import *
from telebot_deye_helper import *

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from custom_registers import CustomRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_fake_message import TelebotFakeMessage
from telebot_menu_item_handler import TelebotMenuItemHandler
from deye_registers_factory import DeyeRegistersFactory

class TelebotMenuWritableRegisters(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot, is_authorized_func, is_writable_register_allowed_func):
    self.bot: telebot.TeleBot = bot
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

      try:
        # remove keyboard from message
        self.bot.edit_message_reply_markup(chat_id = call.message.chat.id,
                                           message_id = call.message.message_id,
                                           reply_markup = None)
      except Exception:
        # Ignore exceptions (e.g., "message is not modified")
        pass

      msg_time = datetime.fromtimestamp(call.message.date, tz = timezone.utc)
      if datetime.now(timezone.utc) - msg_time > timedelta(hours = 24):
        self.bot.send_message(call.message.chat.id, 'Command is expired')
        return

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

      # handle special values
      if value == sync_inverter_time_str:
        # run /sync_time command
        message = TelebotFakeMessage(cast(telebot.types.Message, call.message),
                                     f'/{TelebotMenuItem.deye_sync_time.command}', call.from_user)
        self.bot.process_new_messages([message])
        return

      try:
        text = self.process_read_write_register_step2(register, value)
        self.bot.send_message(call.message.chat.id, text, parse_mode = 'HTML')
      except Exception as e:
        self.bot.send_message(call.message.chat.id, str(e))

      self.bot.clear_step_handler_by_chat_id(call.message.chat.id)

    return textwrap.dedent('''\
    import telebot
    from telebot_deye_helper import *

    @self.bot.message_handler(commands = ['{register_name}'])
    def set_{register_name}(message):
      if not self.is_authorized(message, self.command):
        return

      if not self.is_writable_register_allowed(message.from_user.id, self.command, '{register_name}'):
        available_registers = self.get_available_registers(message.from_user.id)
        self.bot.send_message(message.chat.id, f'You can\\'t change <b>{register_description}</b>. Available registers to change:\\n{{available_registers}}', parse_mode = 'HTML')
        return

      register = self.registers.{register_name}_register

      try:
        text = self.process_read_write_register_step1(register)
        keyboard = self.create_keyboard_for_register(register)
        sent = self.bot.send_message(message.chat.id, text, reply_markup = keyboard, parse_mode='HTML')
        self.bot.register_next_step_handler(message, set_{register_name}_step2, sent.message_id)
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
  
    def set_{register_name}_step2(message, message_id: int):
      if not self.is_authorized(message, self.command):
        return

      # remove buttons from previous message
      try:
        self.bot.edit_message_reply_markup(
            chat_id = message.chat.id,
            message_id = message_id,
            reply_markup = None
        )
      except Exception:
        # Ignore exceptions (e.g., "message is not modified")
        pass

      # if we received new command, process it
      if message.text.startswith('/'):
        self.bot.process_new_messages([message])
        return

      register = self.registers.{register_name}_register

      try:
        text = self.process_read_write_register_step2(register, message.text)
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
  ''').format(register_name = register.name, register_description = register.description)

  def create_keyboard_for_register(self, register: DeyeRegister):
    if register.name == self.registers.inverter_system_time_register.name:
      time_diff = register.value - datetime.now()
      diff_seconds = int(abs(time_diff.total_seconds()))
      if diff_seconds > inverter_system_time_need_sync_difference_sec:
        return build_keyboard_for_register(register, [
          [sync_inverter_time_str],
        ])
      else:
        return None

    return get_keyboard_for_register(self.registers, register)

  def process_read_write_register_step1(self, register: DeyeRegister) -> str:
    loggers = DeyeLoggers()

    def creator(prefix) -> DeyeRegisters:
      return CustomRegisters([register], prefix)

    try:
      holder = DeyeRegistersHolder(loggers = [loggers.master], register_creator = creator, **holder_kwargs)
      holder.connect_and_read()
    except Exception as e:
      raise Exception(str(e))
    finally:
      holder.disconnect()

    result = f'Current <b>{register.description}</b> value: {register.value} {register.suffix}\n'

    if register.min_value != register.max_value:
      result += f'Enter new value (from {register.min_value} to {register.max_value}):'
    else:
      result += f'Enter new value:'

    return result

  def process_read_write_register_step2(self, register: DeyeRegister, text: str) -> str:
    try:
      if type(register.value) is int and register.value == int(text):
        return f'New value ({int(text)}) is the same as old value ({register.value}). Do nothing'

      if type(register.value) is float and register.value == float(text):
        return f'New value ({float(text)}) is the same as old value ({register.value}). Do nothing'

      value = write_register(register, text)
      return f'<b>{register.description}</b> changed to {value} {register.suffix}'
    except Exception as e:
      raise Exception('Error while writing registers: ' + str(e))

  def get_available_registers(self, user_id: int) -> str:
    str = ''
    num = 1
    for register in self.registers.read_write_registers:
      if self.is_writable_register_allowed(user_id, self.command, register.name):
        str += f'<b>{num}. {register.description}:</b>\n'
        str += f'/{register.name}\n'
        num += 1
    return str
