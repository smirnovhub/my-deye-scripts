import logging
import telebot
import traceback

from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_exceptions import DeyeKnownException
from custom_registers import CustomRegisters
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item import TelebotMenuItem
from deye_registers_holder import DeyeRegistersHolder
from deye_registers_factory import DeyeRegistersFactory
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import ask_confirmation
from telebot_advanced_choice import ask_advanced_choice
from telebot_utils import remove_inline_buttons_with_delay
from deye_utils import is_tests_on
from deye_utils import get_test_retry_count

from telebot_constants import (
  undo_button_name,
  undo_button_remove_delay_sec,
  inverter_system_time_does_not_need_sync_threshold_sec,
  inverter_system_time_too_big_difference_sec,
)

from telebot_deye_helper import (
  holder_kwargs,
  get_available_registers,
)

class TelebotMenuSyncTime(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.log = logging.getLogger()
    self.loggers = DeyeLoggers()
    self.auth_helper = TelebotAuthHelper()
    self.registers = DeyeRegistersFactory.create_registers()
    self.register = self.registers.inverter_system_time_register

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_sync_time

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    if not self.auth_helper.is_writable_register_allowed(message.from_user.id, self.register.name):
      available_registers = get_available_registers(self.registers, self.auth_helper, message.from_user.id)
      self.bot.send_message(
        message.chat.id,
        f'You can\'t change <b>{self.register.description}</b>. Available registers to change:\n{available_registers}',
        parse_mode = 'HTML')
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomRegisters([self.register], prefix),
      **holder_kwargs,
    )

    def log_retry(attempt, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                    f'{str(exception)}, retrying...')

    try:
      if is_tests_on():
        retry_count = get_test_retry_count()
        holder.read_registers_with_retry(retry_count = retry_count, on_retry = log_retry)
      else:
        holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    if not isinstance(self.register.value, datetime):
      self.bot.send_message(message.chat.id, 'Register type is not datetime', parse_mode = 'HTML')
      return

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    time_diff = self.register.value - datetime.now()
    diff_seconds = int(abs(time_diff.total_seconds()))
    if diff_seconds > inverter_system_time_too_big_difference_sec:
      ask_confirmation(
        self.bot, message.chat.id, f'<b>Warning!</b> '
        f'Difference between inverter time and current time is too big:\n'
        f'Current time: <b>{now}</b>\n'
        f'Inverter time: <b>{self.register.value.strftime("%Y-%m-%d %H:%M:%S")}</b>\n'
        f'The difference is about {diff_seconds} seconds.\n'
        f'<b>Are you sure to sync inverter time?</b>', self.on_user_confirmation)
    elif diff_seconds > inverter_system_time_does_not_need_sync_threshold_sec:
      self.on_user_confirmation(message.chat.id, True)
    else:
      self.bot.send_message(message.chat.id, 'The inverter time is already synced', parse_mode = 'HTML')

  def on_user_confirmation(self, chat_id: int, result: bool):
    if result:
      try:
        old_value = self.register.value
        value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # should be local to avoid issues with locks
        holder = DeyeRegistersHolder(
          loggers = [self.loggers.master],
          **holder_kwargs,
        )

        def log_retry(attempt, exception):
          self.log.info(f'{type(self).__name__}: an exception occurred while writing registers: '
                        f'{str(exception)}, retrying...')

        try:
          if is_tests_on():
            result = holder.write_register_with_retry(
              self.register,
              value,
              retry_count = 10,
              on_retry = log_retry,
            )
          else:
            result = holder.write_register(self.register, value)
        finally:
          holder.disconnect()

        text = f'<b>{self.register.description}</b> changed from {old_value} to {result} {self.register.suffix}'

        sent = ask_advanced_choice(
          self.bot,
          chat_id,
          text,
          {undo_button_name: f'/{self.register.name} {old_value}'},
          max_per_row = 2,
        )

        remove_inline_buttons_with_delay(
          bot = self.bot,
          chat_id = chat_id,
          message_id = sent.message_id,
          delay = undo_button_remove_delay_sec,
        )

      except DeyeKnownException as e:
        self.bot.send_message(chat_id, str(e))
      except Exception as e:
        self.bot.send_message(chat_id, str(e))
        print(traceback.format_exc())
    else:
      self.bot.send_message(chat_id, 'Time sync cancelled')
