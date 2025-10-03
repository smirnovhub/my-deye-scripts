import logging
import telebot

from typing import List

from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_advanced_choice import ask_advanced_choice
from telebot_user_choices_helper import row_break_str
from telebot_utils import is_test_run

from telebot_deye_helper import (
  holder_kwargs,
  get_register_values,
  get_choices_of_inverters,
)

from telebot_constants import (
  sync_inverter_time_button_name,
  inverter_system_time_need_sync_difference_sec,
)

class TelebotMenuMasterBase(TelebotMenuItemHandler):
  def __init__(
    self,
    bot: telebot.TeleBot,
    registers: DeyeRegisters,
    all_command: TelebotMenuItem,
    master_command: TelebotMenuItem,
    slave_command: TelebotMenuItem,
  ):
    super().__init__(bot)
    self.log = logging.getLogger()
    self.loggers = DeyeLoggers()
    self.registers = registers
    self.all_command = all_command
    self.master_command = master_command
    self.slave_command = slave_command

  @property
  def command(self) -> TelebotMenuItem:
    return self.master_command

  def get_commands(self) -> List[telebot.types.BotCommand]:
    master_name = self.loggers.master.name
    return [
      telebot.types.BotCommand(command = self.command.command.format(master_name),
                               description = self.command.description.format(master_name.title())),
    ]

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda _: self.registers,
      **holder_kwargs,
    )

    def log_retry(attempt, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                    f'{str(exception)}, retrying...')

    try:
      if is_test_run():
        holder.read_registers_with_retry(retry_cout = 10, on_retry = log_retry)
      else:
        holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    choices = get_choices_of_inverters(
      user_id = message.from_user.id,
      all_command = self.all_command,
      master_command = self.master_command,
      slave_command = self.slave_command,
    )

    if abs(holder.master_registers.inverter_system_time_diff_register.value
           ) > inverter_system_time_need_sync_difference_sec:
      # add line break for keyboard
      choices[row_break_str] = row_break_str
      # add time sync command
      choices[sync_inverter_time_button_name] = f'/{TelebotMenuItem.deye_sync_time.command}'

    info = get_register_values(holder.master_registers.all_registers)

    ask_advanced_choice(
      self.bot,
      message.chat.id,
      f'<b>Inverter: {self.loggers.master.name}</b>\n{info}',
      choices,
      max_per_row = 2,
    )
