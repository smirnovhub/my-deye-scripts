import os
import time
import random
import logging

from datetime import datetime
from typing import IO, Any, Optional

from deye_utils import DeyeUtils
from deye_file_lock import DeyeFileLock
from deye_base_locker import DeyeBaseLocker
from deye_file_with_lock import DeyeFileWithLock

from lock_exceptions import (
  DeyeLockTimeoutException,
  DeyeLockAlreadyAcquiredException,
  DeyeLockNotHeldException,
)

class DeyeFileLocker(DeyeBaseLocker):
  """
  Handles exclusive file locking with optional logging and file trimming.

  This class allows safe access to a file by acquiring an exclusive lock,
  waiting for it if necessary, and releasing it after use. It can log actions
  to a separate log file and optionally print messages to the console. 

  Features:
      - Acquire an exclusive lock on a file with timeout support.
      - Release the lock safely.
      - Trim log files to a maximum size, keeping only the most recent entries.
      - Verbose logging for debugging and monitoring.
      - Cross-platform safe file locking via `flock`.

  Parameters:
      name (str): Name identifier for logging purposes.
      path (str): Path to the file to lock.
      verbose (bool, optional): Whether to print log messages to console.
                                Defaults to False.
  """
  def __init__(self, name: str, path: str, verbose: bool = False) -> None:
    self._name: str = name
    self._path: str = path
    self._verbose: bool = verbose
    self._lockfile: Optional[IO[Any]] = None
    self._timedout: bool = False
    self._logger = logging.getLogger()

    # Ensure lock file exists
    DeyeUtils.ensure_dir_and_file_exists(path, dir_mode = 0o777, file_mode = 0o666)

    self._rnd: int = random.randint(1000000, 9999999)
    self._log_filename: str = f'{os.path.dirname(path)}/locker.log'

    DeyeUtils.ensure_dir_and_file_exists(self._log_filename, dir_mode = 0o777, file_mode = 0o666)

  def acquire(self, timeout: int = 15) -> None:
    """
    Acquire an exclusive lock on the file.
    Waits up to `timeout` seconds before raising an exception.

    Parameters:
        timeout (int): Maximum time in seconds to wait for the lock.

    Raises:
        DeyeFileLockingException: If lock could not be acquired within timeout.
    """
    if self._lockfile is not None:
      self._log(f"{self._name}: WARNING: lock is already acquired on {self._path}")
      raise DeyeLockAlreadyAcquiredException(f"{type(self).__name__}: lock is already acquired on {self._path}")

    self._trim_file(self._log_filename, 1024 * 1024)

    self._lockfile = open(self._path, "a+")
    self._acquire_time = time.time()
    self._timedout = False

    warning_printed = False

    while True:
      try:
        # Try exclusive lock, non-blocking
        DeyeFileLock.flock(self._lockfile, DeyeFileLock.LOCK_EX | DeyeFileLock.LOCK_NB)
        if warning_printed:
          elapsed = time.time() - self._acquire_time
          self._log(f"{self._name}: acquired exclusive lock on {self._path} after {round(elapsed, 2)} sec")
        else:
          self._log(f"{self._name}: acquired exclusive lock on {self._path}")
        return
      except (BlockingIOError, PermissionError):
        if not warning_printed:
          self._log(f"{self._name}: lock is busy, waiting up to {timeout} seconds...")
          warning_printed = True

        elapsed = time.time() - self._acquire_time
        if elapsed >= timeout:
          self._log(f"{self._name}: timeout after {timeout} sec while waiting for lock on {self._path}")
          self._lockfile.close()
          self._lockfile = None
          self._timedout = True
          raise DeyeLockTimeoutException(
            f"{type(self).__name__}: timeout after {timeout} sec while waiting for lock on {self._path}")
        # wait before retrying
        time.sleep(random.uniform(0.15, 0.3))

  def release(self) -> None:
    """
    Release the acquired lock and close the file.
    Logs the elapsed time the lock was held.
    """
    if self._lockfile is not None:
      DeyeFileLock.flock(self._lockfile, DeyeFileLock.LOCK_UN)
      self._lockfile.close()
      self._lockfile = None
      elapsed = time.time() - self._acquire_time
      self._log(f"{self._name}: released lock on {self._path} after {round(elapsed, 2)} sec")
    elif not self._timedout:
      self._log(f"{self._name}: WARNING: tried to release lock on {self._path}, but no lock was held")
      raise DeyeLockNotHeldException(
        f"{type(self).__name__}: tried to release lock on {self._path}, but no lock was held")

  def _log(self, message: str) -> None:
    """
    Log a message to the locker log file and optionally print it.

    Parameters:
        message (str): The message to log.
    """
    now = datetime.now()
    date = now.strftime(f'[{DeyeUtils.time_format_str}]')

    with DeyeFileWithLock(self._log_filename, "a") as f:
      f.write(f'{date} [{self._rnd}] {message}\n')

    if self._verbose:
      self._logger.info(message)

  def _trim_file(self, filename: str, trim_size: int) -> None:
    """
    Trim the file to a specified size, keeping only the last `trim_size` bytes.
    Skips trimming if file is not larger than 120% of `trim_size`.

    Parameters:
        filename (str): Path to the file to trim.
        trim_size (int): Maximum size of the file after trimming in bytes.
    """
    max_size = int(trim_size * 1.2)
    file_size = os.path.getsize(filename)
    if file_size <= max_size:
      return # trimming not needed

    with open(filename, "rb+") as f:
      try:
        # Try to acquire exclusive lock (non-blocking)
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_EX | DeyeFileLock.LOCK_NB)
      except BlockingIOError:
        # Someone else is working with file - do nothing
        if self._verbose:
          self._logger.error(f"Could not lock {filename}, skipping trim")
        return

      try:
        # Move to position where last `max_size` bytes start
        f.seek(-trim_size, os.SEEK_END)
        data = f.read()

        # Rewrite file with only last `max_size` bytes
        f.seek(0)
        f.write(data)
        f.truncate()
        if self._verbose:
          self._logger.info(f"Trimmed {filename} to {trim_size} bytes")
      finally:
        # Always release lock
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)
