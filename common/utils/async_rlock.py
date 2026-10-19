import asyncio

from typing import Optional

class AsyncRLock:
  """
  Asynchronous reentrant lock for asyncio.
  Allows the same task to acquire the lock multiple times recursively.
  """
  def __init__(self):
    self._lock = asyncio.Lock()
    self._owner: Optional[asyncio.Task] = None
    self._count: int = 0

  async def acquire(self) -> None:
    current = asyncio.current_task()
    if self._owner == current:
      self._count += 1
      return

    await self._lock.acquire()

    self._owner = current
    self._count = 1

  def release(self) -> None:
    current = asyncio.current_task()
    if self._owner != current:
      raise RuntimeError("Lock is not owned by the current task")

    self._count -= 1

    if self._count == 0:
      self._owner = None
      self._lock.release()

  async def __aenter__(self):
    await self.acquire()
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    self.release()
