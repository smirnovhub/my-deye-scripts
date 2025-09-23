import os
import time
import telebot
import subprocess

from telebot_menu_item import TelebotMenuItem
from deye_file_with_lock import DeyeFileWithLock
from deye_utils import ensure_file_exists
from telebot_advanced_choice import ask_advanced_choice
from telebot_constants import git_repository_remote_check_period_sec

class TelebotRemoteUpdateChecker:
  """
  This class provides functionality for checking whether the remote Git repository
  has updates available for the Telebot project. It tracks the last time the user
  was asked about remote updates and prompts the user via Telegram messages to
  update the bot when remote changes are detected.

  File-based locking is used to safely read/write the timestamp of the last update check.
  """
  def __init__(self):
    self.locker = DeyeFileWithLock()
    self.ask_file_name = 'data/last_remote_update_ask_time.txt'
    ensure_file_exists(self.ask_file_name)

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
    last_ask_time = self._load_last_remote_update_ask_time()
    if time.time() - last_ask_time < git_repository_remote_check_period_sec:
      # Too soon since the last check; skip
      return False

    # Save the current check time
    self._save_last_remote_update_ask_time(time.time())

    # Check if the remote repository is up to date
    if not self._is_repository_up_to_date():
      # Prompt the user to update the bot
      ask_advanced_choice(
        bot,
        message.chat.id,
        '<b>Telebot has updates. Do you want to update it now?</b>',
        {
          'Yes, update now': f'/{TelebotMenuItem.update_and_restart.command}',
          'No, update later': f'{message.text}',
        },
      )

      return True

    return False

  def _is_repository_up_to_date(self) -> bool:
    """
    Check if the local repository is up to date with the remote.

    This runs `git remote show origin` and searches for the phrase 'up to date'
    in the output.

    Returns:
        bool: True if the repository is synchronized, False otherwise.

    Raises:
        subprocess.CalledProcessError: If the git command fails.
    """
    try:
      current_dir = os.path.dirname(__file__)
      # Run 'git remote show origin' to get information about remote branches
      result = subprocess.run(["git", "-C", current_dir, "remote", "show", "origin"],
                              check = True,
                              capture_output = True,
                              text = True)

      output = result.stdout.lower() # Convert output to lowercase for case-insensitive search

      # If 'up to date' appears in the output, the local branch is synchronized
      return 'up to date' in output
    except subprocess.CalledProcessError as e:
      # Print the error message if the git command fails
      print("Error executing 'git remote show origin'")
      print(e.stderr)
      raise

  def _load_last_remote_update_ask_time(self) -> float:
    """
    Load the timestamp of the last time the user was asked about remote updates.

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
      print('Error while loading last remote update ask time')
      raise
    finally:
      self.locker.close_file()

  def _save_last_remote_update_ask_time(self, time: float):
    """
    Save the timestamp of the last remote update check.

    Args:
        time (float): The timestamp to save, in seconds since epoch.

    Raises:
        Exception: If the file cannot be opened or written.
    """
    try:
      sfile = self.locker.open_file(self.ask_file_name, 'w')
      sfile.write(str(int(time)))
    except Exception:
      print('Error while saving last remote update ask time')
      raise
    finally:
      self.locker.close_file()
