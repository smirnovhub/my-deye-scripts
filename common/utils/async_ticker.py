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
    self._logger = logging.getLogger()

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
      while True:
        # Calculate how long to wait until the next tick
        wait_time = max(0.0, next_tick - time.time())

        await asyncio.sleep(wait_time)

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
