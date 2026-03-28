import os
import time
import logging

from typing import IO, Any, Optional

from deye_file_lock import DeyeFileLock
from lock_exceptions import DeyeLockTimeoutException

class DeyeFileWithLock:
  """
  Provides a context for safely accessing files with advisory locks.

  This class ensures that files are locked correctly for reading or writing
  on Unix-like systems using `fcntl`. It supports both shared (read) and
  exclusive (write) locks, with optional retry logic and timeout handling.

  Features:
      - Acquire exclusive or shared locks with automatic retries.
      - Open files in read, write, or append modes while holding appropriate locks.
      - Release locks automatically when closing the file.
      - Raise `DeyeFileLockingException` if a lock cannot be acquired within the timeout.
  """
  def __init__(
    self,
    path: str,
    mode: str,
    encoding: str = "utf-8",
    timeout: int = 15,
  ):
    self._sfile: Optional[IO[Any]] = None
    self._path: str = path
    self._mode: str = mode
    self._encoding = encoding
    self._timeout: int = timeout
    self._lock_name: Optional[str] = None
    self._logger = logging.getLogger()

  def __enter__(self) -> IO[Any]:
    # Initialize file opening and locking when entering the context
    return self.open_file(self._path, self._mode, self._timeout)

  def __exit__(self, exc_type, exc_val, exc_tb):
    # Ensure the file is closed and lock is released when exiting the context
    self.close_file()

  def _acquire_lock_with_retry(
    self,
    file_obj: Optional[IO[Any]],
    lock_type: int,
    timeout: int = 15,
  ) -> None:
    """
    Acquire a file lock with retries up to the specified timeout.

    Args:
        file_obj (IOBase): Open file object to lock.
        lock_type (int): Lock type, either fcntl.LOCK_SH (shared) or fcntl.LOCK_EX (exclusive).
        timeout (int, optional): Maximum time in seconds to wait for lock acquisition. Defaults to 15.

    Raises:
        DeyeFileLockingException: If the lock cannot be acquired within the timeout.
    """
    if file_obj is None:
      return

    start_time = time.time()
    warning_printed = False
    self._lock_name = "exclusive" if lock_type == DeyeFileLock.LOCK_EX else "shared"

    while True:
      try:
        DeyeFileLock.flock(file_obj, lock_type | DeyeFileLock.LOCK_NB)

        elapsed = round(time.time() - start_time, 1)
        if warning_printed:
          self._logger.info(f"Acquired {self._lock_name} lock on {self._path} after {elapsed} sec")
        else:
          self._logger.info(f"Acquired {self._lock_name} lock on {self._path}")

        return
      except BlockingIOError:
        if not warning_printed:
          self._logger.info(f"{self._lock_name} lock is busy, waiting up to {timeout} seconds...")
          warning_printed = True

        if time.time() - start_time >= timeout:
          self._logger.error(f"{self._lock_name}: timeout while waiting for lock on {self._path}")
          if self._sfile:
            self._sfile.close()
            self._sfile = None
          raise DeyeLockTimeoutException(f"{self._lock_name}: Timeout while waiting for lock on {self._path}")
        time.sleep(0.25)

  def open_file(
    self,
    path: str,
    mode: str,
    timeout: int = 15,
  ) -> IO[Any]:
    """
    Open a file with proper locking applied based on the access mode.

    For 'w' or 'a' modes, an exclusive lock is acquired. For read modes, a shared lock is acquired.

    Args:
        path (str): Path to the file to open.
        mode (str): File mode, e.g., 'r', 'w', 'a', etc.
        timeout (int, optional): Maximum time in seconds to wait for lock acquisition. Defaults to 15.

    Returns:
        IOBase: The open file object with a lock held.

    Raises:
        DeyeFileLockingException: If the lock cannot be acquired within the timeout.
    """
    self._path = path

    if "w" in mode or "a" in mode:
      # Write/append mode: open file for read/write (a+) and lock exclusively
      self._sfile = open(path, "a+", encoding = self._encoding)
      self._acquire_lock_with_retry(self._sfile, DeyeFileLock.LOCK_EX, timeout)

      # Position file pointer according to mode
      if "w" in mode:
        self._sfile.seek(0)
        self._sfile.truncate(0) # Truncate file after acquiring lock
      elif "a" in mode:
        self._sfile.seek(0, os.SEEK_END) # Move pointer to end for append
    else:
      # Read or read/write without explicit write intent: shared lock
      self._sfile = open(path, mode, encoding = self._encoding)
      self._acquire_lock_with_retry(self._sfile, DeyeFileLock.LOCK_SH, timeout)

    return self._sfile

  def close_file(self) -> None:
    """
    Release the lock and close the file if it is open.
    """
    if self._sfile:
      DeyeFileLock.flock(self._sfile, DeyeFileLock.LOCK_UN)
      self._sfile.close()
      self._sfile = None
      self._logger.info(f"Released {self._lock_name} lock on {self._path}")
