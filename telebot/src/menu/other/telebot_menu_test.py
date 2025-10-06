from io import BufferedReader
import os
import sys
import time
import subprocess
import zipfile
import telebot
import datetime

from typing import Dict, List, TextIO

from deye_file_locker import DeyeFileLocker
from telebot_menu_item import TelebotMenuItem
from testable_telebot import TestableTelebot
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_local_update_checker import TelebotLocalUpdateChecker
from telebot_progress_message import TelebotProgressMessage
from telebot_advanced_choice import ButtonChoice, ask_advanced_choice
from deye_utils import format_timedelta
from deye_file_lock import lock_path

class TelebotMenuTest(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.update_checker = TelebotLocalUpdateChecker()
    self.progress = TelebotProgressMessage(bot)
    lockfile = os.path.join(lock_path, 'teletest.lock')
    self.locker = DeyeFileLocker('teletest', lockfile)
    self.tests_path = '../test/src'

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.test

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    scripts = [
      'deye_multi_inverter_test.py',
      'deye_registers_cache_test.py',
      'deye_single_inverter_test.py',
      'deye_write_registers_test.py',
      'telebot_test.py',
    ]

    all_tests = 'all_tests'

    log_file = 'data/deye_test_log.txt'

    os.environ['BOT_API_TEST_TOKEN'] = self.bot.token

    try:
      self.locker.acquire()
    except Exception:
      self.progress.hide()
      self.progress.show(message.chat.id, 'Tests are already running')
      return

    options: Dict[str, str] = {all_tests: all_tests}
    options.update({s.replace('.py', ''): s for s in scripts})

    def on_choice(chat_id: int, choice: ButtonChoice):
      try:
        self.locker.acquire()
      except Exception:
        self.progress.hide()
        self.progress.show(message.chat.id, 'Tests are already running')
        return

      all_start_time = datetime.datetime.now()
      tests = scripts if choice.data == all_tests else [choice.data]

      try:
        failed_count = self.run_tests(message.chat.id, log_file, tests)
      except Exception as e:
        time.sleep(1)
        t = format_timedelta(datetime.datetime.now() - all_start_time, add_seconds = True)
        self.send_results(message.chat.id, log_file, f'Tests failed after {t}. Check test log for details: {str(e)}')
        self.progress.hide()
        return
      finally:
        try:
          self.locker.release()
        except Exception:
          pass

      time.sleep(1)

      t = format_timedelta(datetime.datetime.now() - all_start_time, add_seconds = True)

      if failed_count == len(tests):
        self.send_results(message.chat.id, log_file, f'<b>All tests failed</b> after {t}. Check test log for details.')
      elif failed_count > 0:
        self.send_results(
          message.chat.id, log_file, f"<b>{failed_count} test(s) failed</b> and "
          f"{len(scripts) - failed_count} test(s) completed successfully in {t}. Check test log for details.")
      else:
        self.send_results(message.chat.id, log_file, f'All tests completed successfully in {t}.')

      self.progress.hide()

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

  def run_tests(
    self,
    chat_id: int,
    log_file: str,
    scripts: List[str],
  ) -> int:
    failed_count = 0
    last_iteration_time = time.time()
    with open(log_file, 'w', encoding = 'utf-8') as f:
      try:
        for i, script in enumerate(scripts):
          if i > 0:
            self.write_and_flush(f, "\n")

          start_time = datetime.datetime.now()
          test_name = script.replace('.py', '')

          self.write_and_flush(f, f"--- RUNNING [{i + 1}/{len(scripts)}] {test_name} ---\n\n")

          time.sleep(1)
          self.progress.hide()
          self.progress.show(chat_id, f'[{i + 1}/{len(scripts)}] Running: {test_name}')

          try:
            result = subprocess.run(
              [sys.executable, "-u", os.path.join(self.tests_path, script)],
              stdout = f,
              stderr = subprocess.STDOUT,
              text = True,
            )
          except Exception as e:
            self.write_and_flush(f, f"An exception while running {test_name}: {e}\n")
            t = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
            self.bot.send_message(
              chat_id,
              f'[{i + 1}/{len(scripts)}] <b>Failed</b> after {t}: {test_name}',
              parse_mode = 'HTML',
            )
            failed_count += 1
            continue

          if result.returncode != 0:
            msg = f"Error: {test_name} exited with code {result.returncode}. Tests failed."
            self.write_and_flush(f, f"{msg}\n")
            t = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
            self.bot.send_message(chat_id,
                                  f'[{i + 1}/{len(scripts)}] <b>Failed</b> after {t}: {test_name}',
                                  parse_mode = 'HTML')
            failed_count += 1
            continue

          # Ensure at least X seconds since the previous iteration
          elapsed = time.time() - last_iteration_time
          if elapsed < 10:
            time.sleep(10 - elapsed)

          last_iteration_time = time.time()
          t = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)
          self.bot.send_message(chat_id,
                                f'[{i + 1}/{len(scripts)}] <b>Success</b> after {t}: {test_name}',
                                parse_mode = 'HTML')

        t = format_timedelta(datetime.datetime.now() - start_time, add_seconds = True)

        if failed_count > 0:
          self.write_and_flush(
            f, f"\n{failed_count} test(s) failed and "
            f"{len(scripts) - failed_count} test(s) completed successfully in {t}.\n")
        else:
          self.write_and_flush(f, f"\nAll tests completed successfully in {t}.\n")

        return failed_count
      except Exception as e:
        self.write_and_flush(f, f'\nAn exception occurred while running tests: {str(e)}\n')
        raise

  def write_and_flush(self, f: TextIO, text: str) -> None:
    """Write text to file, flush Python and OS buffers."""
    f.write(text)
    f.flush()
    try:
      os.fsync(f.fileno())
    except Exception:
      pass

  def send_results(self, chat_id: int, log_file: str, message: str):
    files = [
      log_file,
      TestableTelebot.telebot_test_log_file_name,
    ]

    self.zip_and_send(chat_id, files, message)

  def zip_and_send(self, chat_id: int, files: List[str], message: str) -> None:
    """
    Send a list of files and their zip archives as a media group with a caption.
    Non-existing files are ignored.
    """
    media_group: List[telebot.types.InputMediaDocument] = []
    zip_files: List[str] = []
    open_files: List[BufferedReader] = []

    for file_path in files:
      if not os.path.exists(file_path):
        continue # skip non-existing files

      file_base = os.path.splitext(file_path.replace("_", "-"))[0]
      file_ext = os.path.splitext(file_path)[1]
      name_with_date = f"{file_base}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
      zip_file = f"{name_with_date}.zip"

      # Create zip
      with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, arcname = os.path.basename(f'{name_with_date}{file_ext}'))

      zip_files.append(zip_file)

      f = open(zip_file, 'rb')
      open_files.append(f)

      # Add zip file
      media_group.append(
        telebot.types.InputMediaDocument(telebot.types.InputFile(
          f,
          file_name = os.path.basename(zip_file),
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
    for log_file in zip_files + files:
      try:
        os.remove(log_file)
      except Exception:
        pass
