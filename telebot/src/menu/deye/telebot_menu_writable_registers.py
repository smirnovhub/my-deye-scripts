import telebot
import textwrap
import traceback

from typing import Dict, List
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from custom_registers import CustomRegisters
from deye_exceptions import DeyeKnownException
from deye_exceptions import DeyeValueException
from deye_registers_holder import DeyeRegistersHolder
from telebot_fake_message import TelebotFakeMessage
from telebot_menu_item import TelebotMenuItem
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item_handler import TelebotMenuItemHandler
from deye_registers_factory import DeyeRegistersFactory
from telebot_advanced_choice import ask_advanced_choice
from telebot_constants import undo_button_remove_delay_sec

from telebot_utils import (
  get_inline_button_by_text,
  remove_inline_buttons_with_delay,
)

from telebot_constants import (
  undo_button_name,
  buttons_remove_delay_sec,
  sync_inverter_time_button_name,
  inverter_system_time_need_sync_difference_sec,
)

from telebot_deye_helper import (
  holder_kwargs,
  build_keyboard_for_register,
  get_keyboard_for_register,
  get_available_registers,
)

class TelebotMenuWritableRegisters(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.loggers = DeyeLoggers()
    self.registers = DeyeRegistersFactory.create_registers()
    self.auth_helper = TelebotAuthHelper()

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
            sync_inverter_time_button_name: f'/{TelebotMenuItem.deye_sync_time.command}'
          },
        ])
      else:
        return None

    return get_keyboard_for_register(self.registers, register)

  def process_read_write_register_step1(self, message: telebot.types.Message, register_name: str, next_step_callback):
    if not self.is_authorized(message):
      return

    pos = message.text.find(' ')
    if message.from_user and pos != -1:
      param = message.text[pos + 1:].strip()
      if param:
        fake_message = TelebotFakeMessage(
          message,
          param,
          message.from_user,
        )
        self.process_read_write_register_step2(fake_message, message.id, register_name)
        return

    register = self.registers.get_register_by_name(register_name)
    if register is None:
      self.bot.send_message(message.chat.id, f'Register {register_name} not found')
      self.bot.clear_step_handler_by_chat_id(message.chat.id)
      return

    if not self.auth_helper.is_writable_register_allowed(message.from_user.id, register_name):
      available_registers = get_available_registers(self.registers, self.auth_helper, message.from_user.id)
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
    if not self.is_authorized(message):
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

    # Pass dict to change value inside the method
    old_register_value: Dict[str, int] = {}

    try:
      text = self.write_register(register, message.text, old_register_value)
    except DeyeKnownException as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      print(traceback.format_exc())
      return

    old_value = old_register_value[register.name]
    is_undo_button_pressed = get_inline_button_by_text(message, undo_button_name) is not None

    if old_value != register.value and not is_undo_button_pressed:
      sent = ask_advanced_choice(
        self.bot,
        message.chat.id,
        text,
        {undo_button_name: f'/{register.name} {old_value}'},
        max_per_row = 2,
      )

      remove_inline_buttons_with_delay(
        bot = self.bot,
        chat_id = message.chat.id,
        message_id = sent.message_id,
        delay = undo_button_remove_delay_sec,
      )
    else:
      self.bot.send_message(message.chat.id, text, parse_mode = 'HTML')

  def get_register_value(self, register: DeyeRegister):

    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomRegisters([register], prefix),
      **holder_kwargs,
    )

    try:
      holder.connect_and_read()
    finally:
      holder.disconnect()

    result = f'Current <b>{register.description}</b> value: {register.value} {register.suffix}\n'

    if register.min_value != register.max_value:
      result += f'Enter new value (from {register.min_value} to {register.max_value}):'
    else:
      result += f'Enter new value:'

    return result

  def write_register(self, register: DeyeRegister, text: str, old_register_value: Dict[str, int]) -> str:
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomRegisters([register], prefix),
      **holder_kwargs,
    )

    try:
      holder.connect_and_read()
      old_register_value[register.name] = register.value

      suffix = f' {register.suffix}'.rstrip()

      if type(register.value) is int and register.value == int(text):
        raise DeyeValueException(f'New value ({int(text)}{suffix}) is the same as old value. Nothing changed')

      if type(register.value) is float and register.value == float(text):
        raise DeyeValueException(f'New value ({float(text)}{suffix}) is the same as old value. Nothing changed')

      if type(register.value) is str and register.value == str(text):
        raise DeyeValueException(f'New value ({str(text)}{suffix}) is the same as old value. Nothing changed')

      value = holder.write_register(register, text)
    finally:
      holder.disconnect()

    return f'<b>{register.description}</b> changed to {value} {register.suffix}'
