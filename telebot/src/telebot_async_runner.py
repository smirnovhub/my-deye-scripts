import asyncio
import logging
import threading

from typing import Coroutine, Any
from concurrent.futures import Future

class TelebotAsyncRunner:
  def __init__(self, logger: logging.Logger) -> None:
    self._logger = logger
    self._loop = asyncio.new_event_loop()
    self._thread = threading.Thread(
      target = self._run_loop,
      daemon = True,
    )
    self._thread.start()

  def run(self, coro: Coroutine[Any, Any, Any]) -> Future:
    """
    Submit coroutine to the event loop
    """
    future = asyncio.run_coroutine_threadsafe(coro, self._loop)

    def _callback(f: Future) -> None:
      try:
        f.result()
      except Exception:
        self._logger.error("Async task failed", exc_info = True)

    future.add_done_callback(_callback)
    return future

  def stop(self) -> None:
    """
    Graceful shutdown of the loop
    """
    self._loop.call_soon_threadsafe(self._loop.stop)
    self._thread.join(timeout = 5)

  def _run_loop(self) -> None:
    asyncio.set_event_loop(self._loop)
    self._loop.run_forever()
