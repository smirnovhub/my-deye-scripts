import telebot
import urllib.parse

from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import UserChoices
from countdown_with_cancel import CountdownWithCancel

class TelebotMenuRestart(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.restart

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    UserChoices.ask_confirmation(
      self.bot, message.chat.id, f'<b>Warning!</b> Bot process will be killed '
      'and will <b>not</b> restart automatically if you didn\'t configure it '
      'for automatic restart. <b>Do you really want to kill bot proccess?</b>', self.on_user_confirmation)

  def on_user_confirmation(self, chat_id: int, result: bool):
    if result:
      CountdownWithCancel.show_countdown(
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
                          f'{urllib.parse.unquote(CommonUtils.clock_face_one_oclock)} Restarting telebot...',
                          parse_mode = 'HTML')
    TelebotUtils.stop_bot(self.bot)

  def on_cancel(self, chat_id: int):
    self.bot.send_message(chat_id, 'Restart cancelled')
