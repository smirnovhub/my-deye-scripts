import asyncio
import logging
import signal
import time

from datetime import timedelta

class AsyncTicker:
  def __init__(
    self,
    period: timedelta,
    align_with_period: bool = False,
  ):
    self._period = period
    self._align_with_period = align_with_period
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

  async def __aiter__(self):
    """
    Async generator ticking every self._period seconds in real time.
    Each tick aligns to the next wall-clock boundary and accounts for the duration of yield.
    """
    self._setup_signals()
    period_sec = self._period.total_seconds()

    self._logger.info("AsyncTicker started.")

    # Calculate the initial tick time
    next_tick = time.time()
    if self._align_with_period:
      # Align to the next multiple of period_sec from the epoch
      next_tick = next_tick - (next_tick % period_sec) + period_sec
    else:
      next_tick += period_sec

    while not self._stop_event.is_set():
      # Calculate how long to wait until the next tick
      wait_time = max(0.0, next_tick - time.time())
      try:
        # Wait either until the stop_event is set or the timeout expires
        await asyncio.wait_for(self._stop_event.wait(), timeout = wait_time)
        break # stop_event triggered
      except asyncio.TimeoutError:
        pass # Timeout expired, tick should occur

      yield # Yield control to the calling loop

      # Move next_tick to the next period boundary relative to previous tick
      next_tick += period_sec
      # If we are behind (yield took too long), jump to the next future boundary
      now = time.time()
      if next_tick <= now:
        skipped = int((now - next_tick) // period_sec) + 1
        next_tick += skipped * period_sec
