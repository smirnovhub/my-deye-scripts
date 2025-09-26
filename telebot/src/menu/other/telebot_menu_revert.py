import os
import re
import telebot
import urllib.parse

from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_local_update_checker import TelebotLocalUpdateChecker
from telebot_user_choices import ask_confirmation
from countdown_with_cancel import countdown_with_cancel
from telebot_advanced_choice import ask_advanced_choice
from common_utils import clock_face_one_oclock

from telebot_git_helper import (
  stash_push,
  stash_pop,
  stash_clear,
  is_repository_up_to_date,
  revert_to_revision,
  get_last_commits,
  get_last_commit_hash,
  get_last_commit_hash_and_comment,
)

class TelebotMenuRevert(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.update_checker = TelebotLocalUpdateChecker()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.revert

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    try:
      if not is_repository_up_to_date():
        last_commit = get_last_commit_hash_and_comment()
        last_commit = last_commit.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.bot.send_message(
          message.chat.id,
          "Can't revert because repository is not up to date. "
          f'Pls run <b>/update</b> and then try again. You are currently on:\n<b>{last_commit}</b>',
          parse_mode = "HTML",
        )
        self.update_checker.check_for_local_updates(self.bot, message.chat.id, force = True)
        return
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    pos = message.text.find(' ')
    if pos != -1:
      commit_hash = re.sub(r'[^0-9a-f]', '', message.text[pos + 1:])
      if len(commit_hash) >= 32:
        self.do_revert(message.chat.id, commit_hash)
        return

    try:
      last_commits = get_last_commits()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return

    if last_commits:
      ask_advanced_choice(
        self.bot,
        message.chat.id,
        'Enter commit hash to revert to:',
        {
          item: f"/revert {hash}"
          for item, hash in last_commits.items()
        },
        max_per_row = 1,
      )
    else:
      self.bot.send_message(message.chat.id, 'Enter commit hash to revert to:')

    self.bot.register_next_step_handler(message, self.handle_step2)

  def handle_step2(self, message: telebot.types.Message):
    # If we received new command, skip it
    if message.text.startswith('/'):
      return

    if message.text is not None:
      commit_hash = re.sub(r'[^0-9a-f]', '', message.text)
      if len(commit_hash) >= 32:
        self.do_revert(message.chat.id, message.text)
      else:
        self.bot.send_message(message.chat.id, f'Wrong commit hash')

  def do_revert(self, chat_id: int, commit_hash: str):
    try:
      stash_clear()

      last_commit_hash = get_last_commit_hash()
      if last_commit_hash == commit_hash:
        self.bot.send_message(chat_id, f'You are already on {commit_hash[:7]}')
        return

      stash_push()
      result = revert_to_revision(commit_hash)
      stash_pop()
    except Exception as e:
      self.bot.send_message(chat_id, str(e))
      return

    self.bot.send_message(chat_id, result)

    ask_confirmation(
      self.bot,
      chat_id,
      'Revert completed. For the changes to take effect, need to restart the bot. '
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
