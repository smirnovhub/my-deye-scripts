import time
import asyncio
import logging

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
    self._logger = logging.getLogger()
    self._logger.setLevel(logging.INFO)

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
    period_sec = self._period.total_seconds()
    self._logger.info("AsyncTicker started.")

    # Calculate the initial tick time
    next_tick = time.time()
    if self._align_with_period:
      # Align to the next multiple of period_sec from the epoch
      next_tick = next_tick - (next_tick % period_sec) + period_sec
    else:
      next_tick += period_sec

    try:
      while not self._stop_event.is_set():
        # Calculate how long to wait until the next tick
        wait_time = max(0.0, next_tick - time.time())

        await self._wait_with_cancellation(wait_time)

        yield # Yield control to the calling loop

        # Move next_tick to the next period boundary relative to previous tick
        next_tick += period_sec
        # If we are behind (yield took too long), jump to the next future boundary
        now = time.time()
        if next_tick <= now:
          skipped = int((now - next_tick) // period_sec) + 1
          next_tick += skipped * period_sec
    except asyncio.CancelledError:
      self._logger.info("AsyncTicker cancelled.")
      raise
    finally:
      self._logger.info("AsyncTicker finished.")

  async def _wait_with_cancellation(self, wait_time: float) -> None:
    """
    Wait for the given time using an absolute end time to prevent drift.
    """
    check_time_sec = 1.0
    # Calculate the exact timestamp when we should finish
    end_time = time.monotonic() + wait_time

    while True:
      now = time.monotonic()
      remaining = end_time - now

      if remaining <= 0:
        break

      # Sleep for the check interval or the actual remaining time
      timeout = min(check_time_sec, remaining)

      try:
        # Wait for the event with a calculated timeout
        await asyncio.wait_for(self._stop_event.wait(), timeout = timeout)
        # Event was set, exit the loop
        break
      except (asyncio.TimeoutError, asyncio.exceptions.TimeoutError):
        # Continue to the next iteration to re-calculate remaining time
        continue
