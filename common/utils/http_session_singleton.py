import requests
import atexit
import logging
import threading

from typing import Optional

class HttpSessionSingleton:
  """
  Thread-safe singleton for a shared requests.Session.
  Automatically closes the session at program exit.
  """
  _instance: Optional["HttpSessionSingleton"] = None
  _lock = threading.Lock()

  def __new__(cls):
    # Double-checked locking
    if cls._instance is None:
      with cls._lock:
        if cls._instance is None:
          cls._instance = super().__new__(cls)
          cls._instance._init_session()
    return cls._instance

  def _init_session(self):
    self._session = requests.Session()
    logging.getLogger().info("Created shared HTTP session.")
    atexit.register(self._close_session)

  def _close_session(self):
    if self._session:
      logger = logging.getLogger()
      logger.info("Closing shared HTTP session...")
      self._session.close()

  @property
  def session(self) -> requests.Session:
    return self._session
