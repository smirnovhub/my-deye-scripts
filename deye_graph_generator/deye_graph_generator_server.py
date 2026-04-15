import os
import sys
import asyncio
import logging
import traceback
import signal

from datetime import timedelta

common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../common"))

for dir, dirs, files in os.walk(common_path):
  if dir not in sys.path:
    sys.path.append(dir)

from log_utils import LogUtils
from async_ticker import AsyncTicker
from graph_generator import GraphGenerator
from src.graph_generator_config import GraphGeneratorConfig
from http_session_singleton_async import HttpSessionSingletonAsync

config = GraphGeneratorConfig()

LOG_DIR = f"data/{config.LOG_NAME}"

logger = LogUtils.setup_hourly_overwrite_file_logger(
  log_dir = LOG_DIR,
  log_file_template = "graph_generator-{0}.log",
)

graph_generator = GraphGenerator(
  config = config,
  logger = logger,
)

async def run_ticker(ticker: AsyncTicker):
  """Wrapper to run the AsyncTicker and handle CancelledError"""
  try:
    async for _ in ticker:
      try:
        await graph_generator.main_logic()
        logger.info('-------------------------------------')
      except Exception:
        callstack = traceback.format_exc()
        logger.error(f"Error during task execution: {callstack}")
  except asyncio.CancelledError:
    logger.info("Ticker task received CancelledError")
    raise
  finally:
    logger.info("Ticker task finished")

async def main():
  ticker = AsyncTicker(
    period = timedelta(minutes = config.PERIOD),
    run_delay = timedelta(seconds = config.DELAY),
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

  logger.info("Graph Generator server started.")
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

    logger.info("Graph Generator server stopped.")
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
