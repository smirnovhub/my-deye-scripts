import telebot

from typing import List
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler

class TelebotMenuUnknownCommandHandler(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.unknown_command_echo

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return []

  def register_handlers(self):
    @self.bot.message_handler(func = lambda message: message.text and message.text.startswith('/'))
    def handle(message: telebot.types.Message):
      if not self.is_authorized(message.from_user.id, message.chat.id):
        return

      self.bot.send_message(message.chat.id, f"Unknown command: /\u200B{message.text.strip('/')}")
