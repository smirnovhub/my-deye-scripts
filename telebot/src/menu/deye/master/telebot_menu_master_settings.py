from typing import List
import telebot

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from master_settings_registers import MasterSettingsRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler

from telebot_deye_helper import (
  holder_kwargs,
  get_register_values,
)

class TelebotMenuMasterSettings(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.loggers = DeyeLoggers()
    self.holder = DeyeRegistersHolder(loggers = [self.loggers.master],
                                      register_creator = lambda prefix: MasterSettingsRegisters(prefix),
                                      **holder_kwargs)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_master_settings

  def get_commands(self) -> List[telebot.types.BotCommand]:
    master_name = self.loggers.master.name
    return [
      telebot.types.BotCommand(command = self.command.command.format(master_name),
                               description = self.command.description.format(master_name.title())),
    ]

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    try:
      self.holder.connect_and_read()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      self.holder.disconnect()

    master_name = self.loggers.master.name.title()
    info = get_register_values(self.holder.master_registers.all_registers)
    self.bot.send_message(message.chat.id, f'<b>{master_name} inverter settings:</b>\n{info}', parse_mode = 'HTML')
