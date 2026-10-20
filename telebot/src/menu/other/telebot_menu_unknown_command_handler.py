import telebot

from telebot.async_telebot import AsyncTeleBot

from typing import List

from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuUnknownCommandHandler(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: AsyncTeleBot,
  ):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.unknown_command_echo

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return []

  def register_handlers(self) -> None:
    @self.bot.message_handler(func = lambda message: message.text and message.text.startswith('/'))
    async def handle(message: telebot.types.Message):
      if not await self.is_authorized(message):
        return

      await self.bot.send_message(message.chat.id, f"Unknown command: /\u200B{message.text.strip('/')}")
