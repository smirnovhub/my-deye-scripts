import os
import telebot
import urllib.parse

from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import ask_confirmation
from countdown_with_cancel import countdown_with_cancel
from common_utils import clock_face_one_oclock

class TelebotMenuRestart(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.restart

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    ask_confirmation(
      self.bot, message.chat.id, f'<b>Warning!</b> Bot process will be killed '
      'and will <b>not</b> restart automatically if you didn\'t configure it '
      'for automatic restart. <b>Do you really want to kill bot proccess?</b>', self.on_user_confirmation)

  def on_user_confirmation(self, chat_id: int, result: bool):
    if result:
      countdown_with_cancel(
        bot = self.bot,
        chat_id = chat_id,
        text = 'Will restart in: ',
        seconds = 5,
        on_finish = self.on_finish,
        on_cancel = self.on_cancel,
      )
    else:
      self.bot.send_message(chat_id, 'Restart cancelled')

  def on_finish(self, chat_id: int):
    self.bot.send_message(chat_id,
                          f'{urllib.parse.unquote(clock_face_one_oclock)} Restarting the bot...',
                          parse_mode = 'HTML')
    os._exit(1)

  def on_cancel(self, chat_id: int):
    self.bot.send_message(chat_id, 'Restart cancelled')
