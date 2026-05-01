import time
import logging
import telebot

from env_utils import EnvUtils
from git_helper import GitHelper
from deye_utils import DeyeUtils
from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants
from telebot_menu_item import TelebotMenuItem
from deye_file_with_lock import DeyeFileWithLock
from telebot_command_choice import CommandChoice

class TelebotRemoteUpdateChecker:
  """
  This class provides functionality for checking whether the remote Git repository
  has updates available for the Telebot project. It tracks the last time the user
  was asked about remote updates and prompts the user via Telegram messages to
  update the bot when remote changes are detected.

  File-based locking is used to safely read/write the timestamp of the last update check.
  """
  def __init__(self):
    self._git_helper = GitHelper()
    self._logger = logging.getLogger()

    data_dir = TelebotUtils.get_data_dir()
    self._ask_file_name = f'{data_dir}/last_remote_update_ask_time.txt'

    DeyeUtils.ensure_dir_and_file_exists(self._ask_file_name)

  def is_on_branch(self):
    if EnvUtils.is_tests_on():
      return True

    last_ask_time = self._load_last_remote_update_ask_time()
    if time.time() - last_ask_time < TelebotConstants.git_repository_remote_check_period_sec:
      # Too soon since the last check; skip
      return True

    try:
      result = self._git_helper.get_current_branch_name() != 'HEAD'
      if not result:
        # Save the current check time
        self._save_last_remote_update_ask_time(time.time())
      return result
    except Exception:
      # Save the current check time
      self._save_last_remote_update_ask_time(time.time())
      return False

  def check_for_remote_updates(self, bot: telebot.TeleBot, message: telebot.types.Message) -> bool:
    """
    Check if the remote repository has updates and prompt the user to update the bot.

    - If the last check was too recent, returns False without prompting.
    - If remote updates are detected, prompts the user via Telegram to update the bot.

    Args:
        bot (telebot.TeleBot): The Telebot instance for sending messages.
        message (telebot.types.Message): The incoming message object from the user.

    Returns:
        bool: True if a user prompt was sent, False otherwise.
    """
    if EnvUtils.is_tests_on():
      return False

    last_ask_time = self._load_last_remote_update_ask_time()
    if time.time() - last_ask_time < TelebotConstants.git_repository_remote_check_period_sec:
      # Too soon since the last check; skip
      return False

    # Save the current check time
    self._save_last_remote_update_ask_time(time.time())

    # Check if the remote repository is up to date
    if not self._git_helper.is_repository_up_to_date():
      # Prompt the user to update the bot
      CommandChoice.ask_command_choice(
        bot,
        message.chat.id,
        '<b>Telebot has updates. Do you want to update it now?</b>',
        {
          'Yes, update now': f'/{TelebotMenuItem.update.command}',
          'No, update later': f'{message.text}',
        },
      )

      return True

    return False

  def _load_last_remote_update_ask_time(self) -> float:
    """
    Load the timestamp of the last time the user was asked about remote updates.

    Returns:
        float: The timestamp in seconds since epoch, or 0 if the file is empty.

    Raises:
        Exception: If the file cannot be opened or read.
    """
    with DeyeFileWithLock(self._ask_file_name, "r") as f:
      try:
        str_val = f.readline().strip()
        return float(str_val) if str_val else 0
      except Exception:
        self._logger.info('Error while loading last remote update ask time')
        raise

  def _save_last_remote_update_ask_time(self, time: float):
    """
    Save the timestamp of the last remote update check.

    Args:
        time (float): The timestamp to save, in seconds since epoch.

    Raises:
        Exception: If the file cannot be opened or written.
    """
    with DeyeFileWithLock(self._ask_file_name, "w") as f:
      try:
        f.write(str(int(time)))
      except Exception:
        self._logger.info('Error while saving last remote update ask time')
        raise
