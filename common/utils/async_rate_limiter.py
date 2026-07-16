import time
import asyncio
import logging

from datetime import timedelta

class AsyncRateLimiter:
  """
  A reusable asynchronous rate limiter that enforces a minimum time delay 
  between operations using native __aenter__ and __aexit__ lifecycle methods.
  """
  def __init__(
    self,
    delay: timedelta,
    name: str = "rate_limiter",
    verbose: bool = False,
  ):
    """
    Initialize the rate limiter.

    Args:
        delay_between_requests (timedelta): Minimum duration required between operations.
        name (str): Identifier used for logging purposes.
        verbose (bool): If True, enables detailed logging for sleep events.
    """
    self._delay = delay.total_seconds()
    self._name = name
    self._verbose = verbose
    self._last_event_time = 0.0
    self._logger = logging.getLogger()

  async def __aenter__(self) -> None:
    elapsed = time.monotonic() - self._last_event_time

    if elapsed < self._delay:
      remaining_sleep = self._delay - elapsed

      if self._verbose:
        self._logger.info(f"{self._name}: sleeping for {remaining_sleep:.3f}s because of rate limit protection")

      await asyncio.sleep(remaining_sleep)

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    self._last_event_time = time.monotonic()
