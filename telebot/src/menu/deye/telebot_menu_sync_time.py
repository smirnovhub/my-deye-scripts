import telebot
import traceback

from datetime import datetime

from deye_utils import DeyeUtils
from telebot_deye_helper import TelebotDeyeHelper
from telebot_utils import TelebotUtils
from deye_exceptions import DeyeKnownException
from custom_single_registers import CustomSingleRegisters
from telebot_constants import TelebotConstants
from telebot_menu_item import TelebotMenuItem
from deye_registers_holder import DeyeRegistersHolder
from deye_registers import DeyeRegisters
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import UserChoices
from telebot_command_choice import CommandChoice

class TelebotMenuSyncTime(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.registers = DeyeRegisters()
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
      available_registers = TelebotDeyeHelper.get_available_registers(
        self.registers,
        self.auth_helper,
        message.from_user.id,
      )

      self.bot.send_message(
        message.chat.id,
        f"You can't change <b>{self.register.description}</b>. "
        f"Available registers to change:\n{available_registers}",
        parse_mode = 'HTML',
      )
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(self.register, prefix),
      **dict(
        TelebotDeyeHelper.holder_kwargs,
        caching_time = 15,
      ),
    )

    try:
      holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    if not isinstance(self.register.value, datetime):
      self.bot.send_message(
        message.chat.id,
        f'Register type is not {datetime.__name__}',
        parse_mode = 'HTML',
      )
      return

    now = DeyeUtils.get_current_time().strftime(DeyeUtils.time_format_str)
    time_diff = self.register.value - DeyeUtils.get_current_time()
    diff_seconds = int(abs(time_diff.total_seconds()))
    if diff_seconds > TelebotConstants.inverter_system_time_too_big_difference_sec:
      UserChoices.ask_confirmation(
        self.bot,
        message.chat.id,
        f'<b>Warning!</b> '
        f'Difference between inverter time and current time is too big:\n'
        f'Current time: <b>{now}</b>\n'
        f'Inverter time: <b>{self.register.value.strftime(DeyeUtils.time_format_str)}</b>\n'
        f'The difference is about {diff_seconds} seconds.\n'
        f'<b>Are you sure to sync inverter time?</b>',
        self.on_user_confirmation,
      )
    elif diff_seconds > TelebotConstants.inverter_system_time_need_sync_difference_sec:
      self.on_user_confirmation(message.chat.id, True)
    else:
      self.bot.send_message(
        message.chat.id,
        'The inverter time is already synced',
        parse_mode = 'HTML',
      )

  def on_user_confirmation(self, chat_id: int, result: bool):
    if result:
      try:
        old_value = self.register.value
        value = DeyeUtils.get_current_time().strftime(DeyeUtils.time_format_str)

        # should be local to avoid issues with locks
        holder = DeyeRegistersHolder(
          loggers = [self.loggers.master],
          **TelebotDeyeHelper.holder_kwargs,
        )

        try:
          result = holder.write_register(self.register, value)
        finally:
          holder.disconnect()

        text = (f'<b>{self.register.description}</b> changed from {old_value} '
                f'to {result} {self.register.suffix}')

        sent = CommandChoice.ask_command_choice(
          self.bot,
          chat_id,
          text,
          {TelebotConstants.undo_button_name: f'/{self.register.name} {old_value}'},
          max_per_row = 2,
        )

        TelebotUtils.remove_inline_buttons_with_delay(
          bot = self.bot,
          chat_id = chat_id,
          message_id = sent.message_id,
          delay = TelebotConstants.undo_button_remove_delay_sec,
        )

      except DeyeKnownException as e:
        self.bot.send_message(chat_id, str(e))
      except Exception as e:
        self.bot.send_message(chat_id, str(e))
        print(traceback.format_exc())
    else:
      self.bot.send_message(chat_id, 'Time sync cancelled')
