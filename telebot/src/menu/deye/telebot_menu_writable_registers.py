import logging
import telebot
import textwrap
import traceback

from typing import Any, List, Optional
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from custom_registers import CustomRegisters
from deye_exceptions import DeyeKnownException
from deye_exceptions import DeyeValueException
from deye_base_enum import DeyeBaseEnum
from deye_registers_holder import DeyeRegistersHolder
from telebot_fake_message import TelebotFakeMessage
from telebot_menu_item import TelebotMenuItem
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item_handler import TelebotMenuItemHandler
from deye_registers_factory import DeyeRegistersFactory
from telebot_user_choices import ask_confirmation
from telebot_advanced_choice import ask_advanced_choice
from telebot_constants import undo_button_remove_delay_sec
from telebot_utils import get_test_retry_count

from telebot_utils import (
  is_test_run,
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
    self.log = logging.getLogger()
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

  def get_writable_register_handler(self, register: DeyeRegister) -> str:
    return textwrap.dedent('''\
    @self.bot.message_handler(commands = ['{register_name}'])
    def set_{register_name}(message):
      self.process_read_write_register_step1(message, '{register_name}', set_{register_name}_step2)

    def set_{register_name}_step2(message, message_id: int):
      self.process_read_write_register_step2(message, message_id, '{register_name}')
  ''').format(register_name = register.name)

  def create_keyboard_for_register(self, register: DeyeRegister) -> Optional[telebot.types.InlineKeyboardMarkup]:
    if isinstance(register.value, datetime) and register.name == self.registers.inverter_system_time_register.name:
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
      self.bot.clear_step_handler_by_chat_id(message.chat.id)
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

    if not message.text:
      self.bot.send_message(message.chat.id, f'Register value is empty')
      return

    # if we received new command, process it
    if message.text.startswith('/'):
      self.bot.process_new_messages([message])
      return

    register = self.registers.get_register_by_name(register_name)
    if register is None:
      self.bot.send_message(message.chat.id, f'Register {register_name} not found')
      self.bot.clear_step_handler_by_chat_id(message.chat.id)
      return

    try:
      self.write_register(register, message)
    except DeyeKnownException as e:
      self.bot.send_message(message.chat.id, str(e), parse_mode = 'HTML')
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e), parse_mode = 'HTML')
      print(traceback.format_exc())

  def get_register_value(self, register: DeyeRegister) -> str:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomRegisters([register], prefix),
      **holder_kwargs,
    )

    def log_retry(attempt, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                    f'{str(exception)}, retrying...')

    try:
      if is_test_run():
        retry_count = get_test_retry_count()
        holder.read_registers_with_retry(retry_count = retry_count, on_retry = log_retry)
      else:
        holder.read_registers()
    finally:
      holder.disconnect()

    result = f'Current <b>{register.description}</b> value: {register.pretty_value} {register.suffix}\n'

    if register.min_value != register.max_value:
      result += f'Enter new value (from {register.min_value} to {register.max_value}):'
    else:
      result += f'Enter new value:'

    return result

  def write_register(
    self,
    register: DeyeRegister,
    message: telebot.types.Message,
  ):
    if message.text is None:
      raise DeyeValueException('Message text is empty')

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomRegisters([register], prefix),
      **holder_kwargs,
    )

    def log_read_retry(attempt, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                    f'{str(exception)}, retrying...')

    def log_write_retry(attempt, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while writing registers: '
                    f'{str(exception)}, retrying...')

    try:
      if is_test_run():
        retry_count = get_test_retry_count()
        holder.read_registers_with_retry(retry_count = retry_count, on_retry = log_read_retry)
      else:
        holder.read_registers()

      value: Any = 0
      suffix = f' {register.suffix}'.rstrip()

      if isinstance(register.value, int):
        try:
          value = int(message.text)
        except Exception:
          raise DeyeValueException(f'Value should be int from {register.min_value} to {register.max_value}')
        if register.value == value:
          raise self.get_nothing_changed_exception(register.value, suffix)
      elif isinstance(register.value, float):
        try:
          value = float(message.text)
        except Exception:
          raise DeyeValueException(f'Value should be float from {register.min_value} to {register.max_value}')
        if register.value == value:
          raise self.get_nothing_changed_exception(register.value, suffix)
      elif isinstance(register.value, DeyeBaseEnum):
        value = register.value.parse(message.text)
        if register.value == value:
          raise self.get_nothing_changed_exception(register.value.pretty, suffix)
      else:
        value = str(message.text)

      if isinstance(value, DeyeBaseEnum) and value.is_unknown:
        raise DeyeValueException(f'Enum value for <b>{register.description}</b> is unknown')

      if str(register.value) == message.text:
        raise self.get_nothing_changed_exception(register.value, suffix)

      old_value = register.value
      old_pretty_value = register.pretty_value

      def on_user_confirmation(chat_id: int, result: bool):
        if not result:
          self.bot.send_message(message.chat.id, 'Nothing changed', parse_mode = 'HTML')
        else:
          try:
            if is_test_run():
              retry_count = get_test_retry_count()
              holder.write_register_with_retry(
                register,
                value,
                retry_count = retry_count,
                on_retry = log_write_retry,
              )
            else:
              holder.write_register(register, value)

            self.print_result_after_write_register(
              register,
              message,
              old_value = old_value,
              old_pretty_value = old_pretty_value,
            )
          except DeyeKnownException as e:
            self.bot.send_message(message.chat.id, str(e))
          except Exception as e:
            self.bot.send_message(message.chat.id, str(e))
            print(traceback.format_exc())
          finally:
            holder.disconnect()

      is_undo_button_pressed = get_inline_button_by_text(message, undo_button_name) is not None

      if isinstance(value, DeyeBaseEnum) and not is_undo_button_pressed and not is_test_run():
        ask_confirmation(
          self.bot,
          message.chat.id,
          f'Do you really want to change <b>{register.description}</b> '
          f'to {value.pretty}{suffix}?',
          on_user_confirmation,
        )
        return

      if is_test_run():
        holder.write_register_with_retry(
          register,
          value,
          retry_count = 10,
          on_retry = log_write_retry,
        )
      else:
        holder.write_register(register, value)

      self.print_result_after_write_register(
        register,
        message,
        old_value = old_value,
        old_pretty_value = old_pretty_value,
      )

    finally:
      holder.disconnect()

  def print_result_after_write_register(
    self,
    register: DeyeRegister,
    message: telebot.types.Message,
    old_value: Any,
    old_pretty_value: str,
  ):
    suffix = f' {register.suffix}'.rstrip()
    text = (f'<b>{register.description}</b> changed from {old_pretty_value} '
            f'to {register.pretty_value}{suffix}')

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

  def get_nothing_changed_exception(self, value: Any, suffix: str) -> Exception:
    return DeyeValueException(f'New value ({str(value)}{suffix}) is '
                              'the same as old value. Nothing changed')
