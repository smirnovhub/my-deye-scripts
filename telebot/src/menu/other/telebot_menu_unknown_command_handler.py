import telebot

from typing import List
from telebot_menu_item import TelebotMenuItem
from telebot_async_runner import TelebotAsyncRunner
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuUnknownCommandHandler(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
    )

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.unknown_command_echo

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return []

  def register_handlers(self) -> None:
    @self.bot.message_handler(func = lambda message: message.text and message.text.startswith('/'))
    def handle(message: telebot.types.Message):
      if not self.is_authorized(message):
        return

      self.bot.send_message(message.chat.id, f"Unknown command: /\u200B{message.text.strip('/')}")
