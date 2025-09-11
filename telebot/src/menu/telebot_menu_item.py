import telebot
from typing import List
from telebot_menu_command import TelebotMenuCommand

class TelebotMenuItem:
  @property
  def command(self) -> TelebotMenuCommand:
    return TelebotMenuCommand.unknown

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return []
  
  def register_handlers(self):
    pass
