import os
import sys
import time
import html
import logging
import signal
import traceback

from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

import telebot

# Should be first in imports list to make possible
# to send error messages if some import fails
from log_utils import LogUtils
from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from telegram_send_message import Telegram
from telebot_async_runner import TelebotAsyncRunner

# Simple and safe way for HTML parse_mode
def escape_html(text: str) -> str:
  # This replaces &, <, and > with &amp;, &lt;, and &gt;
  return html.escape(text)

def main():
  dir_name = TelebotUtils.get_data_dir()
  log_dir_name = os.path.join(dir_name, 'logs')

  logger = LogUtils.setup_hourly_overwrite_file_logger(
    log_dir = log_dir_name,
    log_file_template = "telebot-{0}.log",
  )

  # Create async runner
  runner = TelebotAsyncRunner(logger)

  def graceful_shutdown(signum, frame):
    # Log signal receipt
    logger.info("Telebot is going down...")

    try:
      # Send a final message synchronously
      Telegram.send_private_telegram_message(f"{CommonUtils.large_yellow_circle_emoji} "
                                             "Telebot is going down...")
    except Exception as e:
      # Log error if message fails
      logger.info(f"Failed to send goodbye message: {e}")

    # Stop event loop
    runner.stop()

    # Stop the polling loop
    bot.stop_polling()

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()

    # Exit the process
    sys.exit(0)

  # Register for both manual interrupt and system termination
  signal.signal(signal.SIGINT, graceful_shutdown)
  signal.signal(signal.SIGTERM, graceful_shutdown)

  logger.info('Telebot is starting...')

  try:
    from mytelebot import MyTelebot
    from env_utils import EnvUtils
    from testable_telebot import TestableTelebot

    if EnvUtils.is_tests_on():
      token = EnvUtils.get_telegram_bot_api_test_token()
      bot = TestableTelebot(token)

      mybot = MyTelebot(
        bot = bot,
        runner = runner,
        logger = logger,
      )

      mybot.run_tests()
      sys.exit(0)

    Telegram.send_private_telegram_message(f'{CommonUtils.clock_face_two_oclock_emoji} Telebot is starting...')

    bot = telebot.TeleBot(
      EnvUtils.get_telegram_bot_api_token(),
      num_threads = 10,
    )

    mybot = MyTelebot(
      bot = bot,
      runner = runner,
      logger = logger,
    )

    bot.infinity_polling()
  except Exception as e:
    if not EnvUtils.is_tests_on():
      stack_trace = escape_html(traceback.format_exc()[-2048:])
      Telegram.send_private_telegram_message(f"{CommonUtils.large_red_circle_emoji} "
                                             f"Telebot unexpectedly stopped working:\n"
                                             f"<code>{stack_trace}</code>")
      time.sleep(30)
    raise

if __name__ == "__main__":
  main()
