import os
import telebot
import urllib.parse

from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import ask_confirmation
from common_utils import clock_face_one_oclock

class TelebotMenuRestart(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot, is_authorized_func):
    super().__init__(bot)
    self.is_authorized = is_authorized_func

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.restart

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message, self.command):
      return

    ask_confirmation(
      self.bot, message.chat.id, f'<b>Warning!</b> Bot process will be killed '
      'and will <b>not</b> restart automatically if you didn\'t configure it '
      'for automatic restart. <b>Do you really want to kill bot proccess?</b>', self.on_user_confirmation)

  def on_user_confirmation(self, chat_id: int, result: bool):
    if result:
      self.bot.send_message(chat_id,
                            f'{urllib.parse.unquote(clock_face_one_oclock)} Shutting down the bot...',
                            parse_mode = 'HTML')
      os._exit(1)
    else:
      self.bot.send_message(chat_id, 'Restart cancelled')
