import telebot
import traceback

from typing import List
from telebot_menu_item import TelebotMenuItem
from deye_exceptions import DeyeKnownException

class TelebotMenuItemHandler:
  def __init__(self, bot: telebot.TeleBot):
    self.bot: telebot.TeleBot = bot

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.unknown

  def get_commands(self) -> List[telebot.types.BotCommand]:
    return [
      telebot.types.BotCommand(command = self.command.command, description = self.command.description),
    ]

  def register_handlers(self):
    commands = [cmd.command for cmd in self.get_commands()]

    @self.bot.message_handler(commands = commands)
    def handle(message: telebot.types.Message):
      try:
        self.process_message(message)
      except DeyeKnownException as e:
        self.bot.send_message(message.chat.id, str(e))
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
        print(traceback.format_exc())

  def process_message(self, message: telebot.types.Message):
    raise NotImplementedError(
      f'{self.__class__.__name__}: process_message() for command {self.command.command} is not implemented yet')
