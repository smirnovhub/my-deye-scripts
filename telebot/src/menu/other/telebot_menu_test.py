import os
import re
import sys
import time
import subprocess
import zipfile
import telebot
import datetime

from io import BufferedReader
from urllib.parse import unquote
from typing import Dict, List, TextIO

from deye_file_locker import DeyeFileLocker
from telebot_menu_item import TelebotMenuItem
from testable_telebot import TestableTelebot
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_local_update_checker import TelebotLocalUpdateChecker
from lock_exceptions import DeyeLockAlreadyAcquiredException
from telebot_progress_message import TelebotProgressMessage
from telebot_advanced_choice import ButtonChoice, ask_advanced_choice
from deye_utils import format_timedelta, ensure_dir_exists
from deye_file_lock import lock_path

from common_utils import (
  large_green_circle_emoji,
  large_yellow_circle_emoji,
  white_circle_emoji,
  large_red_circle_emoji,
)

class TelebotMenuTest(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.update_checker = TelebotLocalUpdateChecker()
    self.progress = TelebotProgressMessage(bot)
    lockfile = os.path.join(lock_path, 'teletest.lock')
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

    ensure_dir_exists(self.logs_path)

    scripts = self.find_py_files('../test/src')

    self.remove_logs(scripts)

    all_tests = 'all tests'

    os.environ['BOT_API_TEST_TOKEN'] = self.bot.token

    options: Dict[str, str] = {all_tests: all_tests}
    options.update({os.path.basename(s).replace('.py', '').replace('_', ' '): s for s in scripts})

    def on_choice(chat_id: int, choice: ButtonChoice):
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
      tests = scripts if choice.data == all_tests else [choice.data]

      try:
        failed_count = self.run_tests(message.chat.id, tests)

        time.sleep(1)

        t = format_timedelta(datetime.datetime.now() - all_start_time, add_seconds = True)

        if failed_count == len(tests):
          self.send_results(
            scripts,
            message.chat.id,
            f'{unquote(large_red_circle_emoji)} '
            f'<b>All tests failed</b> after {t}. '
            'Check logs for details.',
          )
        elif failed_count > 0:
          self.send_results(
            scripts,
            message.chat.id,
            f'{unquote(large_yellow_circle_emoji)} '
            f"<b>{failed_count} test(s) failed</b> and "
            f"{len(scripts) - failed_count} test(s) completed successfully in {t}. "
            "Check logs for details.",
          )
        else:
          self.send_results(
            scripts,
            message.chat.id,
            f'{unquote(large_green_circle_emoji)} '
            f'All tests completed successfully in {t}.',
          )
      except Exception as e:
        time.sleep(1)
        t = format_timedelta(datetime.datetime.now() - all_start_time, add_seconds = True)
        self.send_results(
          scripts,
          message.chat.id,
          f'{unquote(large_red_circle_emoji)} '
          f'Tests failed after {t}. '
          'Check test log for details: {str(e)}',
        )

      finally:
        try:
          self.locker.release()
          self.progress.hide()
          self.remove_logs(scripts)
        except Exception:
          pass

    ask_advanced_choice(
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

  def find_py_files(self, base_path: str = ".") -> List[str]:
    """
    Recursively search for Python test files matching patterns:
      - *_test.py
      - *_test_<number>.py
    Returns their relative paths.
    """
    pattern = re.compile(r".*_test(?:_\d+)?\.py$")
    matched_files = []

    base_path = os.path.normpath(base_path)

    for root, _, files in os.walk(base_path):
      for f in files:
        if pattern.match(f):
          rel_path = os.path.relpath(os.path.join(root, f))
          matched_files.append(rel_path)

    matched_files.sort()
    return matched_files

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
          self.running_test = (f'{unquote(white_circle_emoji)} '
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
            t = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
            self.bot.send_message(
              chat_id,
              f'{unquote(large_red_circle_emoji)} '
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
            t = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
            self.bot.send_message(
              chat_id,
              f'{unquote(large_red_circle_emoji)} '
              f'[{i + 1}/{len(scripts)}] '
              f'<b>Failed</b> after {t}: {test_name}',
              parse_mode = 'HTML',
            )
            failed_count += 1
            continue

          t = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)

          # Ensure at least X seconds since the previous iteration
          elapsed = time.time() - last_iteration_time
          if elapsed < 5:
            time.sleep(5 - elapsed)

          self.progress.hide()
          time.sleep(1)

          last_iteration_time = time.time()
          self.bot.send_message(
            chat_id,
            f'{unquote(large_green_circle_emoji)} '
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
    Send a list of files and their zip archives as a media group with a caption.
    Non-existing files are ignored.
    """
    media_group: List[telebot.types.InputMediaDocument] = []
    zip_files: List[str] = []
    open_files: List[BufferedReader] = []

    for script in scripts:
      file_path = os.path.join(self.logs_path, os.path.basename(script).replace('.py', '.log'))
      if not os.path.exists(file_path):
        continue # skip non-existing files

      zip_file = self.create_zip_file(file_path)
      zip_files.append(zip_file)

      f = open(zip_file, 'rb')
      open_files.append(f)

      # Add zip file
      media_group.append(
        telebot.types.InputMediaDocument(telebot.types.InputFile(
          f,
          file_name = os.path.basename(zip_file),
        )))

    if os.path.exists(TestableTelebot.telebot_test_log_file_name):
      telebot_zip_file = self.create_zip_file(TestableTelebot.telebot_test_log_file_name)
      zip_files.append(telebot_zip_file)

      tf = open(telebot_zip_file, 'rb')
      open_files.append(tf)

      # Add zip file
      media_group.append(
        telebot.types.InputMediaDocument(telebot.types.InputFile(
          tf,
          file_name = os.path.basename(telebot_zip_file),
        )))

    if media_group:
      # Add caption to the first file only
      media_group[-1].parse_mode = "HTML"
      media_group[-1].caption = message + ' Log files attached.'
      self.bot.send_media_group(chat_id, list(media_group))
    else:
      self.bot.send_message(chat_id, message, parse_mode = "HTML")

    for of in open_files:
      of.close()

    # Clean up files
    for log_file in zip_files:
      try:
        os.remove(log_file)
      except Exception:
        pass

  def create_zip_file(self, file_path: str) -> str:
    file_base = os.path.splitext(file_path.replace("_", "-"))[0]
    file_ext = os.path.splitext(file_path)[1]
    name_with_date = f"{file_base}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    zip_file_name = f"{name_with_date}.zip"

    # Create zip
    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zf:
      zf.write(file_path, arcname = os.path.basename(f'{name_with_date}{file_ext}'))

    return zip_file_name
