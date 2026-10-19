import os
import sys
import html
import asyncio
import logging
import signal
import traceback

from typing import Optional
from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from telebot.async_telebot import AsyncTeleBot

# Should be first in imports list to make possible
# to send error messages if some import fails
from log_utils import LogUtils
from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from testable_telebot import TestableTelebot
from telegram_send_message_async import TelegramAsync
from http_session_singleton_async import HttpSessionSingletonAsync
from telebot_async_step_manager import TelebotAsyncStepManager

# Simple and safe way for HTML parse_mode
def escape_html(text: str) -> str:
  # This replaces &, <, and > with &amp;, &lt;, and &gt;
  return html.escape(text)

async def main():
  dir_name = TelebotUtils.get_data_dir()
  log_dir_name = os.path.join(dir_name, 'logs')

  logger = LogUtils.setup_hourly_overwrite_file_logger(
    log_dir = log_dir_name,
    log_file_template = "telebot-{0}.log",
  )

  # Initializing global bot variable for access in shutdown
  bot: Optional[AsyncTeleBot] = None

  async def graceful_shutdown():
    # Log signal receipt
    logger.info("Telebot is going down...")

    try:
      # Send a final message synchronously
      await TelegramAsync.send_private_telegram_message(f"{CommonUtils.large_yellow_circle_emoji} "
                                                        "Telebot is going down...")
    except Exception as e:
      # Log error if message fails
      logger.info(f"Failed to send goodbye message: {e}")

    try:
      await HttpSessionSingletonAsync.close_session()
    except Exception:
      logger.error("Failed to close async session", exc_info = True)

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()

    # Stop the event loop and exit
    loop = asyncio.get_event_loop()
    loop.stop()

  # Register signals within the asyncio loop
  loop = asyncio.get_event_loop()

  def handle_exit() -> None:
    asyncio.create_task(graceful_shutdown())

  try:
    for sig in (signal.SIGINT, signal.SIGTERM):
      loop.add_signal_handler(sig, handle_exit)
  except Exception:
    pass

  logger.info('Telebot is starting...')

  try:
    from mytelebot import MyTelebot
    from env_utils import EnvUtils

    if EnvUtils.is_tests_on():
      token = EnvUtils.get_telegram_bot_api_test_token()
      bot = TestableTelebot(token)

      mybot = MyTelebot(
        bot = bot,
        logger = logger,
      )

      await mybot.initialize()
      await mybot.run_tests()

      sys.exit(0)

    await TelegramAsync.send_private_telegram_message(
      f'{CommonUtils.clock_face_two_oclock_emoji} Telebot is starting...')

    bot = AsyncTeleBot(token = EnvUtils.get_telegram_bot_api_token())

    mybot = MyTelebot(
      bot = bot,
      logger = logger,
    )

    TelebotAsyncStepManager.setup(bot)

    await mybot.initialize()

    # Non-blocking infinity polling
    await bot.infinity_polling()

  except Exception as e:
    if not EnvUtils.is_tests_on():
      stack_trace = escape_html(traceback.format_exc()[-2048:])
      await TelegramAsync.send_private_telegram_message(f"{CommonUtils.large_red_circle_emoji} "
                                                        f"Telebot unexpectedly stopped working:\n"
                                                        f"<code>{stack_trace}</code>")
      await asyncio.sleep(60)
    raise

if __name__ == "__main__":
  try:
    asyncio.run(main())
  except (KeyboardInterrupt, SystemExit):
    pass
