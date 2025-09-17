import telebot
from typing import List
from telebot_menu_item import TelebotMenuItem

class TelebotMenuItemHandler:
  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.unknown

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return []

  def register_handlers(self):
    pass
