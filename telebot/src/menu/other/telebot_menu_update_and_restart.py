import os
import re
import telebot
import urllib.parse
import subprocess

from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_user_choices import ask_confirmation
from countdown_with_cancel import countdown_with_cancel
from common_utils import clock_face_one_oclock

class TelebotMenuUpdateAndRestart(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.update_and_restart

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    current_dir = os.path.dirname(__file__)

    try:
      git_result = subprocess.run(['git', '-C', current_dir, 'pull'], capture_output = True, text = True)
    except subprocess.CalledProcessError as e:
      self.bot.send_message(message.chat.id, 'Git pull failed')
      return

    if git_result.returncode != 0:
      if 'would be overwritten' in git_result.stderr:
        self.bot.send_message(message.chat.id, 'Git pull failed: local changes conflict with remote changes')
      else:
        self.bot.send_message(message.chat.id, 'Git pull failed')
      return

    if git_result.stdout.strip().startswith('Already up to date'):
      self.bot.send_message(message.chat.id, 'Already up to date')
      return

    pattern = r'\d+ files? changed.*'
    matches = re.findall(pattern, git_result.stdout)

    for match in matches:
      self.bot.send_message(message.chat.id, match)

    ask_confirmation(
      self.bot,
      message.chat.id,
      'Update completed. For the changes to take effect, need to restart the bot. '
      '<b>Do you want to restart it now?</b>',
      self.on_user_confirmation,
    )

  def on_user_confirmation(self, chat_id: int, result: bool):
    if not result:
      self.bot.send_message(chat_id, 'Restart cancelled')
      return

    countdown_with_cancel(
      bot = self.bot,
      chat_id = chat_id,
      text = 'Will restart in: ',
      seconds = 5,
      on_finish = self.on_finish,
      on_cancel = self.on_cancel,
    )

  def on_finish(self, chat_id: int):
    self.bot.send_message(chat_id,
                          f'{urllib.parse.unquote(clock_face_one_oclock)} Restarting telebot...',
                          parse_mode = 'HTML')
    os._exit(1)

  def on_cancel(self, chat_id: int):
    self.bot.send_message(chat_id, 'Restart cancelled')
