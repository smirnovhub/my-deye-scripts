import telebot

from typing import List

from telebot_utils import TelebotUtils
from deye_registers import DeyeRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_constants import TelebotConstants
from telebot_deye_helper import TelebotDeyeHelper
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_command_choice import CommandChoice

class TelebotMenuAllBase(TelebotMenuItemHandler):
  def __init__(
    self,
    bot: telebot.TeleBot,
    registers: DeyeRegisters,
    all_command: TelebotMenuItem,
    master_command: TelebotMenuItem,
    slave_command: TelebotMenuItem,
  ):
    super().__init__(bot)
    self.registers = registers
    self.all_command = all_command
    self.master_command = master_command
    self.slave_command = slave_command

  @property
  def command(self) -> TelebotMenuItem:
    return self.all_command

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return [
      telebot.types.BotCommand(
        command = self.command.command.format(self.loggers.accumulated_registers_prefix),
        description = self.command.description.format(self.loggers.accumulated_registers_prefix.title()),
      )
    ]

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      register_creator = lambda _: self.registers,
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    choices = TelebotDeyeHelper.get_choices_of_inverters(
      user_id = message.from_user.id,
      all_command = self.all_command,
      master_command = self.master_command,
      slave_command = self.slave_command,
    )

    # add button for time sync if needed
    if abs(holder.master_registers.inverter_system_time_diff_register.value
           ) > TelebotConstants.inverter_system_time_need_sync_difference_sec:
      # add line break for keyboard
      choices[TelebotUtils.row_break_str] = TelebotUtils.row_break_str
      # add time sync command
      choices[TelebotConstants.sync_inverter_time_button_name] = f'/{TelebotMenuItem.deye_sync_time.command}'

    info = TelebotDeyeHelper.get_register_values(holder.accumulated_registers.all_registers)

    CommandChoice.ask_command_choice(
      self.bot,
      message.chat.id,
      f'<b>Inverter: {self.loggers.accumulated_registers_prefix}</b>\n{info}',
      choices,
      max_per_row = 2,
    )
