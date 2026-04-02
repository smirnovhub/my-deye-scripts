import os
import logging

from typing import IO, Any, Optional

from deye_file_lock import DeyeFileLock

class DeyeFileWithLockAsync:
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

  async def __aenter__(self) -> IO[Any]:
    # Initialize file opening and locking when entering the context
    return await self.open_file(self._path, self._mode, self._timeout)

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    # Ensure the file is closed and lock is released when exiting the context
    self.close_file()

  async def open_file(
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
      self._lock_name = "exclusive"
      self._sfile = open(path, "a+", encoding = self._encoding)

      wait_time = await DeyeFileLock.flock_async(self._sfile, DeyeFileLock.LOCK_EX, timeout)

      self._logger.info(f"Acquired {self._lock_name} lock on {self._path} in {wait_time:.3f}s")

      # Position file pointer according to mode
      if "w" in mode:
        self._sfile.seek(0)
        self._sfile.truncate(0) # Truncate file after acquiring lock
      elif "a" in mode:
        self._sfile.seek(0, os.SEEK_END) # Move pointer to end for append
    else:
      # Read or read/write without explicit write intent: shared lock
      self._lock_name = "shared"
      self._sfile = open(path, mode, encoding = self._encoding)

      wait_time = await DeyeFileLock.flock_async(self._sfile, DeyeFileLock.LOCK_SH, timeout)

      self._logger.info(f"Acquired {self._lock_name} lock on {self._path} in {wait_time:.3f}s")

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
