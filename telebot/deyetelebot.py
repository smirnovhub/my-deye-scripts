import os
import sys
import asyncio
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

from telebot.async_telebot import AsyncTeleBot

# Should be first in imports list to make possible
# to send error messages if some import fails
from log_utils import LogUtils
from common_utils import CommonUtils
from telebot_utils import TelebotUtils
from testable_telebot import TestableTelebot
from telegram_send_message_async import TelegramAsync
from http_session_singleton_async import HttpSessionSingletonAsync

async def main():
  dir_name = TelebotUtils.get_data_dir()
  log_dir_name = os.path.join(dir_name, 'logs')

  logger = LogUtils.setup_hourly_overwrite_file_logger(
    log_dir = log_dir_name,
    log_file_template = "telebot-{0}.log",
  )

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
      test_token = EnvUtils.get_telegram_bot_api_test_token()
      test_bot = TestableTelebot(test_token)

      test_telebot = MyTelebot(
        bot = test_bot,
        logger = logger,
      )

      await test_telebot.initialize()
      await test_telebot.run_tests()

      try:
        await test_bot.close_session()
        await HttpSessionSingletonAsync.close_session()
      except Exception:
        logger.error("Failed to close async session", exc_info = True)

      for handler in logging.getLogger().handlers:
        handler.flush()

      sys.stdout.flush()
      sys.stderr.flush()

      sys.exit(0)

    await TelegramAsync.send_private_telegram_message(
      f'{CommonUtils.clock_face_two_oclock_emoji} Telebot is starting...')

    token = EnvUtils.get_telegram_bot_api_token()
    bot = AsyncTeleBot(token = token)

    telebot = MyTelebot(
      bot = bot,
      logger = logger,
    )

    await telebot.initialize()

    # Non-blocking infinity polling
    await bot.infinity_polling()

  except Exception as e:
    if not EnvUtils.is_tests_on():
      stack_trace = TelebotUtils.escape_html(traceback.format_exc()[-2048:])
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
