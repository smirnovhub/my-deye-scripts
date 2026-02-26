import asyncio
import logging
import signal
import traceback

from typing import AsyncGenerator
from datetime import timedelta

class AsyncTicker:
  def __init__(self, period: timedelta):
    self._period = period
    self._stop_event = asyncio.Event()
    self._loop = asyncio.get_running_loop()
    self._logger = logging.getLogger()
    self._logger.setLevel(logging.INFO)

  def _setup_signals(self) -> None:
    """
    Internal method to register system signals.
    """
    def shutdown_handler():
      self._logger.info("Shutdown signal received. Shutting down...")
      self.stop()

    # Register handlers for SIGINT (Ctrl+C) and SIGTERM
    for sig in (signal.SIGINT, signal.SIGTERM):
      try:
        self._loop.add_signal_handler(sig, shutdown_handler)
      except NotImplementedError:
        # Fallback for OS environments without full signal support
        pass

  def stop(self) -> None:
    """
    Public method to stop the ticker manually from code.
    """
    self._stop_event.set()

  async def __aiter__(self) -> AsyncGenerator[None, None]:
    """
    Main logic that allows using the class in 'async for' loops.
    """
    self._setup_signals()

    try:
      while not self._stop_event.is_set():
        try:
          # Yield control to the calling loop
          yield
        except Exception as e:
          # Catch exceptions from main logic to keep the ticker running
          callstack = traceback.format_exc()
          self._logger.error(f"Error during task execution: {callstack}")

        # Wait for next interval or stop signal
        try:
          # The event wait will be interrupted by TimeoutError every 'period' seconds
          await asyncio.wait_for(self._stop_event.wait(), timeout = self._period.total_seconds())
          # If we reach here without timeout, it means stop_event was set
          break
        except (asyncio.TimeoutError, asyncio.exceptions.TimeoutError):
          # Period elapsed, continue to the next iteration
          continue
    finally:
      self._logger.info("AsyncTicker stopped.")
