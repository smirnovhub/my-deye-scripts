import aiohttp
import asyncio
import logging

from typing import Optional

class HttpSessionSingletonAsync:
  """
  Async singleton for a shared aiohttp.ClientSession.
  """
  _lock = asyncio.Lock()
  _instance: Optional["HttpSessionSingletonAsync"] = None
  _session: Optional[aiohttp.ClientSession] = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  @classmethod
  async def get_session(cls) -> aiohttp.ClientSession:
    async with cls._lock:
      if cls._session is None or cls._session.closed:
        timeout = aiohttp.ClientTimeout(total = 10)
        cls._session = aiohttp.ClientSession(timeout = timeout)
        logging.getLogger().info("Created shared aiohttp session.")
    return cls._session

  @classmethod
  async def close_session(cls):
    async with cls._lock:
      if cls._session and not cls._session.closed:
        logging.getLogger().info("Closing shared aiohttp session...")
        await cls._session.close()
        cls._session = None
