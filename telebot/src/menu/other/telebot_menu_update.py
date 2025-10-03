import os
import re
import telebot
import urllib.parse
import subprocess

from telebot_git_exception import TelebotGitException
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_local_update_checker import TelebotLocalUpdateChecker
from telebot_user_choices import ask_confirmation
from countdown_with_cancel import countdown_with_cancel
from common_utils import clock_face_one_oclock
from telebot_utils import stop_bot

from telebot_git_helper import (
  check_git_result_and_raise,
  get_last_commit_hash_and_comment,
)

class TelebotMenuUpdate(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.update_checker = TelebotLocalUpdateChecker()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.update

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if not self.remote_update_checker.is_on_branch():
      self.bot.send_message(message.chat.id, 'Unable to update: the repository is not currently on a branch')
      return

    current_dir = os.path.dirname(__file__)

    try:
      result = subprocess.run(
        ['git', '-C', current_dir, 'pull'],
        capture_output = True,
        text = True,
      )
      check_git_result_and_raise(result)
    except TelebotGitException as e:
      self.bot.send_message(message.chat.id, f'Git pull failed: {str(e)}')
      return

    if 'up to date' in result.stdout.lower():
      try:
        last_commit = get_last_commit_hash_and_comment()
      except Exception as e:
        self.bot.send_message(message.chat.id, str(e))
        return

      last_commit = last_commit.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

      self.bot.send_message(
        message.chat.id,
        'Already up to date. '
        f'You are currently on:\n<b>{last_commit}</b>',
        parse_mode = "HTML",
      )

      self.update_checker.check_for_local_updates(self.bot, message.chat.id, force = True)

      return

    pattern = r'\d+ files? changed.*'
    matches = re.findall(pattern, result.stdout)

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
    stop_bot(self.bot)

  def on_cancel(self, chat_id: int):
    self.bot.send_message(chat_id, 'Restart cancelled')
