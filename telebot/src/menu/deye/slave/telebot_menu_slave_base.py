import re
import logging
import telebot

from typing import List
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_command_choice import ask_command_choice
from telebot_user_choices_helper import row_break_str

from telebot_deye_helper import (
  holder_kwargs,
  get_register_values,
  get_choices_of_inverters,
)

from telebot_constants import (
  sync_inverter_time_button_name,
  inverter_system_time_need_sync_difference_sec,
)

class TelebotMenuSlaveTotalBase(TelebotMenuItemHandler):
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
    return self.slave_command

  def get_commands(self) -> List[telebot.types.BotCommand]:
    commands = []
    for logger in self.loggers.loggers:
      if logger.name != self.loggers.master.name:
        commands.append(
          telebot.types.BotCommand(
            command = self.command.command.format(logger.name),
            description = self.command.description.format(logger.name.title()),
          ))
    return commands

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    command_name = message.text.lstrip('/')

    pattern = re.compile(self.slave_command.command.replace("{0}", r"(.+)"))
    match = pattern.fullmatch(command_name)
    slave_name = match.group(1) if match else command_name

    logger = self.loggers.get_logger_by_name(slave_name)
    if logger is None:
      self.bot.send_message(message.chat.id, f'Logger with name {slave_name} not found')
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [logger],
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
      slave_command = self.slave_command,
    )

    if abs(self.registers.inverter_system_time_diff_register.value) > inverter_system_time_need_sync_difference_sec:
      # add line break for keyboard
      choices[row_break_str] = row_break_str
      # add time sync command
      choices[sync_inverter_time_button_name] = f'/{TelebotMenuItem.deye_sync_time.command}'

    info = get_register_values(holder.all_registers[slave_name].all_registers)

    ask_command_choice(
      self.bot,
      message.chat.id,
      f'<b>Inverter: {slave_name}</b>\n{info}',
      choices,
      max_per_row = 2,
    )
