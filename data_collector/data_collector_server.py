import os
import sys
import asyncio
import logging
import traceback
import signal

from pathlib import Path
from datetime import datetime, timedelta

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from log_utils import LogUtils
from async_ticker import AsyncTicker
from data_collector import main_logic
from data_collector_config import DataCollectorConfig
from telegram_send_message_async import TelegramAsync
from http_session_singleton_async import HttpSessionSingletonAsync

config = DataCollectorConfig()

LOG_DIR = f"data/{config.LOG_NAME}"

logger = LogUtils.setup_hourly_overwrite_file_logger(
  log_dir = LOG_DIR,
  log_file_template = "data-collector-{0}.log",
)

last_success = datetime.now()
last_notification = datetime.now()

async def run_ticker(ticker: AsyncTicker):
  """Wrapper to run the AsyncTicker and handle CancelledError"""
  global last_success, last_notification

  try:
    async for _ in ticker:
      try:
        await main_logic(config = config, logger = logger)
        last_success = datetime.now()
      except Exception:
        callstack = traceback.format_exc()
        logger.error(f"Error during task execution: {callstack}")

        try:
          now = datetime.now()
          last_success_delta = (now - last_success).total_seconds // 60
          last_notification_delta = (now - last_notification).total_seconds // 60

          if last_success_delta >= config.CONN_LOST_NOTIFY_AFTER_MINUTES and \
              last_notification_delta >= config.CONN_LOST_NOTIFY_INTERVAL_MINUTES:
            last_notification = now
            await TelegramAsync.send_private_telegram_message()
        except Exception as e:
          logger.error(f"Error during sending telegram notification: {e}")

  except asyncio.CancelledError:
    logger.info("Ticker task received CancelledError")
    raise
  finally:
    logger.info("Ticker task finished")

async def main():
  ticker = AsyncTicker(
    period = timedelta(seconds = config.DATA_COLLECTING_INTERVAL),
    align_with_period = True,
  )

  ticker_task = asyncio.create_task(run_ticker(ticker))

  # Stop event flag
  stop_event = asyncio.Event()

  def _signal_handler(sig_num, frame):
    logger.info(f"Signal {sig_num} received, shutting down...")
    stop_event.set()
    ticker.stop()

  # Register signals for graceful shutdown
  signal.signal(signal.SIGINT, _signal_handler)
  signal.signal(signal.SIGTERM, _signal_handler)

  logger.info("Data collector server started.")
  config.print_config(logger)
  logger.info('-------------------------------------')
  config.validate_or_exit(logger)

  try:
    # Main loop is waiting for stop event
    await stop_event.wait()
  finally:
    logger.info("Stopping ticker...")
    ticker_task.cancel()
    await asyncio.gather(ticker_task, return_exceptions = True)

    await HttpSessionSingletonAsync.close_session()

    logger.info("Data collector server stopped.")
    logger.info('-------------------------------------')

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()

if __name__ == "__main__":
  config.print_usage(logger)
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    logger.info("KeyboardInterrupt caught, exiting...")
