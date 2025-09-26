import os
import time
from typing import Union
import telebot
import urllib.parse

from deye_file_with_lock import DeyeFileWithLock
from telebot_user_choices import ask_choice
from deye_utils import ensure_file_exists
from countdown_with_cancel import countdown_with_cancel
from telebot_git_helper import get_last_commit_hash
from common_utils import clock_face_one_oclock
from telebot_constants import git_repository_local_check_period_sec

class TelebotLocalUpdateChecker:
  """
  This class provides functionality to check for local changes in the Git repository
  used by the Telebot project. It tracks the last time the user was asked about
  local updates and the last commit hash, and prompts the user via Telegram messages
  to restart the bot when local changes are detected.

  File-based locking is used to safely read/write state files.
  """
  def __init__(self):
    self.locker = DeyeFileWithLock()

    self.ask_file_name = 'data/last_local_update_ask_time.txt'
    self.hash_file_name = 'data/last_commit_hash.txt'

    ensure_file_exists(self.ask_file_name)
    ensure_file_exists(self.hash_file_name)

  def check_for_local_updates(
    self,
    bot: telebot.TeleBot,
    chat_id: int,
    force: bool = False,
    message: Union[telebot.types.Message, None] = None,
  ) -> bool:
    """
    Check if the local repository has changed and prompt the user to restart the bot.

    - If the last check was too recent, returns False without prompting.
    - If changes are detected, prompts the user via Telegram to restart the bot.

    Args:
        bot (telebot.TeleBot): The Telebot instance for sending messages.
        message (telebot.types.Message): The incoming message object from the user.

    Returns:
        bool: True if a user prompt was sent, False otherwise.
    """
    if not force:
      last_ask_time = self._load_last_local_update_ask_time()
      if time.time() - last_ask_time < git_repository_local_check_period_sec:
        # Too soon since the last check; skip
        return False

    # Save the current check time
    self._save_last_local_update_ask_time(time.time())

    # Check if the local repository changed since last run
    if self._is_local_repository_changed():
      # Prompt the user to restart the bot to apply local changes
      yes_choice = 'Yes, restart now'
      no_choice = 'No, restart later'

      def on_choice(chat_id: int, choice: str):
        if choice == 'yes' or choice == yes_choice:
          self._ask_for_restart(bot, chat_id)
        else:
          bot.send_message(chat_id, 'Restart cancelled')
          if message is not None:
            bot.process_new_messages([message])

      ask_choice(
        bot,
        chat_id,
        'The local repository has changed. '
        'For the changes to take effect, need to restart the bot. '
        '<b>Do you want to restart it now?</b>',
        [yes_choice, no_choice],
        on_choice,
        accept_wrong_choice_from_user_input = True,
      )

      return True

    return False

  def update_last_commit_hash(self):
    """
    Update the saved commit hash file with the current HEAD commit hash.
    """
    hash = get_last_commit_hash()
    self._save_last_commit_hash(hash)

  def _ask_for_restart(self, bot: telebot.TeleBot, chat_id: int):
    """
    Prompt the user with a countdown and restart the bot automatically.

    Args:
        bot (telebot.TeleBot): The Telebot instance for sending messages.
        chat_id (int): The Telegram chat ID to send messages to.
    """
    def on_finish(chat_id: int):
      bot.send_message(chat_id,
                       f'{urllib.parse.unquote(clock_face_one_oclock)} Restarting telebot...',
                       parse_mode = 'HTML')
      os._exit(1)

    def on_cancel(chat_id: int):
      bot.send_message(chat_id, 'Restart cancelled')

    countdown_with_cancel(
      bot = bot,
      chat_id = chat_id,
      text = 'Will restart in: ',
      seconds = 5,
      on_finish = on_finish,
      on_cancel = on_cancel,
    )

  def _is_local_repository_changed(self) -> bool:
    """
    Determine if the local repository has changed since the last saved commit hash.

    Returns:
        bool: True if the current commit hash differs from the last saved hash.
    """
    current_hash = get_last_commit_hash()
    last_hash = self._load_last_commit_hash()
    return len(last_hash) > 0 and len(current_hash) > 0 and last_hash != current_hash

  def _load_last_local_update_ask_time(self) -> float:
    """
    Load the timestamp of the last time the user was asked about local updates.

    Returns:
        float: The timestamp in seconds since epoch, or 0 if the file is empty.

    Raises:
        Exception: If the file cannot be opened or read.
    """
    try:
      sfile = self.locker.open_file(self.ask_file_name, 'r')
      str_val = sfile.readline().strip()
      return float(str_val) if str_val else 0
    except Exception:
      print('Error while loading last local update ask time')
      raise
    finally:
      self.locker.close_file()

  def _save_last_local_update_ask_time(self, time: float):
    """
    Save the timestamp of the last local update check.

    Args:
        time (float): The timestamp to save, in seconds since epoch.

    Raises:
        Exception: If the file cannot be opened or written.
    """
    try:
      sfile = self.locker.open_file(self.ask_file_name, 'w')
      sfile.write(str(int(time)))
    except Exception:
      print('Error while saving last local update ask time')
      raise
    finally:
      self.locker.close_file()

  def _load_last_commit_hash(self) -> str:
    """
    Load the last saved commit hash from file.

    Returns:
        str: The commit hash string.

    Raises:
        Exception: If the file cannot be opened or read.
    """
    try:
      sfile = self.locker.open_file(self.hash_file_name, 'r')
      return str(sfile.readline().strip())
    except Exception:
      print('Error while loading last commit hash')
      raise
    finally:
      self.locker.close_file()

  def _save_last_commit_hash(self, hash: str):
    """
    Save the given commit hash to file.

    Args:
        hash (str): The commit hash to save.

    Raises:
        Exception: If the file cannot be opened or written.
    """
    try:
      sfile = self.locker.open_file(self.hash_file_name, 'w')
      sfile.write(hash)
    except Exception:
      print('Error while saving last commit hash')
      raise
    finally:
      self.locker.close_file()
