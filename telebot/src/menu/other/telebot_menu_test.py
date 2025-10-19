import os
import sys
import time
import subprocess
import zipfile
import telebot
import datetime

from urllib.parse import unquote
from typing import Dict, List, TextIO

from deye_utils import DeyeUtils
from common_utils import CommonUtils
from deye_file_lock import DeyeFileLock
from deye_file_locker import DeyeFileLocker
from telebot_menu_item import TelebotMenuItem
from telebot_test_utils import TelebotTestUtils
from testable_telebot import TestableTelebot
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_local_update_checker import TelebotLocalUpdateChecker
from lock_exceptions import DeyeLockAlreadyAcquiredException
from telebot_progress_message import TelebotProgressMessage
from telebot_advanced_choice import AdvancedChoiceButton, AdvancedChoice

class TelebotMenuTest(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.update_checker = TelebotLocalUpdateChecker()
    self.progress = TelebotProgressMessage(bot)
    lockfile = os.path.join(DeyeFileLock.lock_path, 'teletest.lock')
    self.locker = DeyeFileLocker('teletest', lockfile)
    self.logs_path = 'data/logs'
    self.running_test = 'none'

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.test

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    try:
      self.locker.acquire()
    except DeyeLockAlreadyAcquiredException:
      self.progress.hide()
      self.progress.show(message.chat.id, self.running_test)
      return
    except Exception as e:
      self.progress.hide()
      self.bot.send_message(message.chat.id, str(e))
      return

    DeyeUtils.ensure_dir_exists(self.logs_path)

    tests_base_dir = '../test/src'
    scripts = TelebotTestUtils.find_tests(tests_base_dir)

    self.remove_logs(scripts)

    all_tests = 'all tests'

    os.environ['BOT_API_TEST_TOKEN'] = self.bot.token

    options: Dict[str, str] = {all_tests: all_tests}
    options.update({os.path.basename(s).replace('.py', '').replace('_', ' '): os.path.basename(s) for s in scripts})

    def on_choice(chat_id: int, choice: AdvancedChoiceButton):
      try:
        self.locker.acquire()
      except DeyeLockAlreadyAcquiredException:
        self.progress.hide()
        self.progress.show(message.chat.id, self.running_test)
        return
      except Exception as e:
        self.progress.hide()
        self.bot.send_message(message.chat.id, str(e))
        return

      all_start_time = datetime.datetime.now()
      tests = scripts if choice.data == all_tests else [os.path.join(tests_base_dir, choice.data)]

      try:
        failed_count = self.run_tests(message.chat.id, tests)
        t = DeyeUtils.format_timedelta(datetime.datetime.now() - all_start_time, add_seconds = True)

        time.sleep(1)

        if failed_count == len(tests):
          self.send_results(
            scripts,
            message.chat.id,
            f'{unquote(CommonUtils.large_red_circle_emoji)} '
            f'<b>All tests failed</b> after {t}. '
            'Check logs for details.',
          )
        elif failed_count > 0:
          self.send_results(
            scripts,
            message.chat.id,
            f'{unquote(CommonUtils.large_yellow_circle_emoji)} '
            f"<b>{failed_count} test(s) failed</b> and "
            f"{len(scripts) - failed_count} test(s) completed successfully in {t}. "
            "Check logs for details.",
          )
        else:
          self.send_results(
            scripts,
            message.chat.id,
            f'{unquote(CommonUtils.large_green_circle_emoji)} '
            f'All tests completed successfully in {t}.',
          )
      except Exception as e:
        t = DeyeUtils.format_timedelta(datetime.datetime.now() - all_start_time, add_seconds = True)
        time.sleep(1)
        self.bot.send_message(
          message.chat.id,
          f'{unquote(CommonUtils.large_red_circle_emoji)} '
          f'Tests failed after {t}. '
          f'Check log files for details: {str(e)}',
        )

      finally:
        try:
          self.locker.release()
          self.progress.hide()
          self.remove_logs(scripts)
        except Exception:
          pass

    AdvancedChoice.ask_advanced_choice(
      self.bot,
      message.chat.id,
      'Select test to run:',
      options,
      on_choice,
      max_per_row = 1,
    )

    try:
      self.locker.release()
    except Exception:
      pass

  def remove_logs(self, scripts: List[str]):
    for script in scripts:
      log_file = os.path.join(self.logs_path, os.path.basename(script).replace('.py', '.log'))
      try:
        os.remove(log_file)
      except Exception:
        pass

    try:
      os.remove(TestableTelebot.telebot_test_log_file_name)
    except Exception:
      pass

  def run_tests(
    self,
    chat_id: int,
    scripts: List[str],
  ) -> int:
    failed_count = 0
    last_iteration_time = time.time()
    for i, script in enumerate(scripts):
      log_file = os.path.join(self.logs_path, os.path.basename(script).replace('.py', '.log'))
      with open(log_file, 'w', encoding = 'utf-8') as f:
        try:
          start_time = datetime.datetime.now()
          test_name = os.path.basename(script).replace('.py', '').replace('_', ' ')

          self.write_and_flush(f, f"--- RUNNING [{i + 1}/{len(scripts)}] {test_name} ---\n\n")

          time.sleep(1)
          self.running_test = (f'{unquote(CommonUtils.white_circle_emoji)} '
                               f'[{i + 1}/{len(scripts)}] Running: {test_name}')
          self.progress.show(
            chat_id,
            self.running_test,
          )

          time.sleep(1)

          try:
            result = subprocess.run(
              [sys.executable, "-u", script],
              stdout = f,
              stderr = subprocess.STDOUT,
              text = True,
            )
          except Exception as e:
            self.progress.hide()
            time.sleep(1)
            self.write_and_flush(f, f"An exception while running {test_name}: {e}\n")
            t = DeyeUtils.format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
            self.bot.send_message(
              chat_id,
              f'{unquote(CommonUtils.large_red_circle_emoji)} '
              f'[{i + 1}/{len(scripts)}] '
              f'<b>Failed</b> after {t}: {test_name}',
              parse_mode = 'HTML',
            )
            failed_count += 1
            continue

          if result.returncode != 0:
            self.progress.hide()
            time.sleep(1)
            msg = f"Error: {test_name} exited with code {result.returncode}. Tests failed."
            self.write_and_flush(f, f"{msg}\n")
            t = DeyeUtils.format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
            self.bot.send_message(
              chat_id,
              f'{unquote(CommonUtils.large_red_circle_emoji)} '
              f'[{i + 1}/{len(scripts)}] '
              f'<b>Failed</b> after {t}: {test_name}',
              parse_mode = 'HTML',
            )
            failed_count += 1
            continue

          t = DeyeUtils.format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)

          # Ensure at least X seconds since the previous iteration
          elapsed = time.time() - last_iteration_time
          if elapsed < 5:
            time.sleep(5 - elapsed)

          self.progress.hide()
          time.sleep(1)

          last_iteration_time = time.time()
          self.bot.send_message(
            chat_id,
            f'{unquote(CommonUtils.large_green_circle_emoji)} '
            f'[{i + 1}/{len(scripts)}] '
            f'<b>Success</b> after {t}: {test_name}',
            parse_mode = 'HTML',
          )
        except Exception as e:
          self.write_and_flush(f, f'\nAn exception occurred while running tests: {str(e)}\n')
          raise

    time.sleep(1)
    return failed_count

  def write_and_flush(self, f: TextIO, text: str) -> None:
    """Write text to file, flush Python and OS buffers."""
    f.write(text)
    f.flush()
    try:
      os.fsync(f.fileno())
    except Exception:
      pass

  def send_results(self, scripts: List[str], chat_id: int, message: str):
    """
    Collects all available log files related to the provided scripts,
    combines them into a single ZIP archive, sends it to the specified Telegram chat,
    and then removes both the original log files and the created ZIP file.

    Parameters:
      scripts: List[str]
          A list of script file paths (.py) whose corresponding log files should be sent.
      chat_id: int
          The Telegram chat ID where the files will be sent.
      message: str
          The message text that will accompany the sent ZIP file.

    Returns:
      None: The method performs its actions (sending files and cleanup) and does not
    """
    all_log_files: List[str] = []

    # Collect log files from scripts
    for script in scripts:
      file_path = os.path.join(self.logs_path, os.path.basename(script).replace('.py', '.log'))
      if os.path.exists(file_path):
        all_log_files.append(file_path)

    # Add telebot test log if exists
    if os.path.exists(TestableTelebot.telebot_test_log_file_name):
      all_log_files.append(TestableTelebot.telebot_test_log_file_name)

    if not all_log_files:
      self.bot.send_message(chat_id, message, parse_mode = "HTML")
      return

    # Create one combined zip
    zip_file_name = self.create_combined_zip(all_log_files)

    try:
      with open(zip_file_name, 'rb') as f:
        self.bot.send_document(
          chat_id,
          telebot.types.InputFile(f, file_name = os.path.basename(zip_file_name)),
          caption = message + ' Log files attached.',
          parse_mode = "HTML",
        )
    finally:
      try:
        os.remove(zip_file_name)
      except Exception:
        pass

      self.remove_logs(scripts)

  def create_combined_zip(self, files: List[str]) -> str:
    """
    Creates a single ZIP archive containing all specified log files.

    Each file is added to the archive under its base name (without directories)
    to keep the ZIP clean and portable. The resulting ZIP filename includes
    a timestamp to ensure uniqueness.

    Parameters:
      files: List[str]
          A list of absolute paths to the log files that should be included in the archive.

    Returns:
      str: The name of the created ZIP file (relative to the current working directory).
    """
    zip_file_name = os.path.join(
      self.logs_path,
      f"test-logs-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.zip",
    )

    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zf:
      for file_path in files:
        zf.write(file_path, arcname = os.path.basename(file_path))

    return zip_file_name
