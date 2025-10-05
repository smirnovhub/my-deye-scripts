import logging
import telebot

from typing import List
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_command_choice import ask_command_choice

from telebot_deye_helper import (
  holder_kwargs,
  get_choices_of_inverters,
  get_register_values,
)

class TelebotMenuBaseSettings(TelebotMenuItemHandler):
  def __init__(
    self,
    bot: telebot.TeleBot,
    registers: DeyeRegisters,
    main_command: TelebotMenuItem,
    all_command: TelebotMenuItem,
    master_command: TelebotMenuItem,
  ):
    super().__init__(bot)
    self.log = logging.getLogger()
    self.loggers = DeyeLoggers()
    self.registers = registers
    self.main_command = main_command
    self.all_command = all_command
    self.master_command = master_command

  @property
  def command(self) -> TelebotMenuItem:
    return self.main_command

  def get_commands(self) -> List[telebot.types.BotCommand]:
    name = self.loggers.master.name if self.main_command == self.master_command else self.loggers.accumulated_registers_prefix
    return [
      telebot.types.BotCommand(command = self.command.command.format(name),
                               description = self.command.description.format(name.title())),
    ]

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master] if self.main_command == self.master_command else self.loggers.loggers,
      register_creator = lambda _: self.registers,
      **holder_kwargs,
    )

    try:
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
      slave_command = None,
    )

    if self.main_command == self.master_command:
      info = get_register_values(holder.master_registers.all_registers)
      inverter_name = self.loggers.master.name.title()
    else:
      info = get_register_values(holder.accumulated_registers.all_registers)
      inverter_name = self.loggers.accumulated_registers_prefix.title()

    ask_command_choice(
      self.bot,
      message.chat.id,
      f'<b>{inverter_name} settings:</b>\n{info}',
      choices,
      max_per_row = 2,
    )
