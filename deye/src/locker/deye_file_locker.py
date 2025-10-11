import os
import time
import random

from datetime import datetime
from typing import IO, Any, Optional

from deye_utils import DeyeUtils
from deye_file_lock import DeyeFileLock

from lock_exceptions import (
  DeyeLockTimeoutException,
  DeyeLockAlreadyAcquiredException,
  DeyeLockNotHeldException,
)

class DeyeFileLocker:
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
    self.name: str = name
    self.path: str = path
    self.verbose: bool = verbose
    self.lockfile: Optional[IO[Any]] = None
    self.timedout: bool = False

    # Ensure lock file exists
    DeyeUtils.ensure_dir_and_file_exists(path, dir_mode = 0o777, file_mode = 0o666)

    self.rnd: int = random.randint(1000000, 9999999)
    self.log_filename: str = f'{os.path.dirname(path)}/locker.log'

    DeyeUtils.ensure_dir_and_file_exists(self.log_filename, dir_mode = 0o777, file_mode = 0o666)

  def log(self, message: str) -> None:
    """
    Log a message to the locker log file and optionally print it.

    Parameters:
        message (str): The message to log.
    """
    now = datetime.now()
    date = now.strftime(f'[{DeyeUtils.time_format_str}]')

    with open(self.log_filename, "a") as f:
      f.write(f'{date} [{self.rnd}] {message}\n')

    if self.verbose:
      print(message)

  def trim_file(self, filename: str, trim_size: int) -> None:
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
        if self.verbose:
          print(f"Could not lock {filename}, skipping trim")
        return

      try:
        # Move to position where last `max_size` bytes start
        f.seek(-trim_size, os.SEEK_END)
        data = f.read()

        # Rewrite file with only last `max_size` bytes
        f.seek(0)
        f.write(data)
        f.truncate()
        if self.verbose:
          print(f"Trimmed {filename} to {trim_size} bytes")
      finally:
        # Always release lock
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

  def acquire(self, timeout: int = 15) -> None:
    """
    Acquire an exclusive lock on the file.
    Waits up to `timeout` seconds before raising an exception.

    Parameters:
        timeout (int): Maximum time in seconds to wait for the lock.

    Raises:
        DeyeFileLockingException: If lock could not be acquired within timeout.
    """
    if self.lockfile is not None:
      self.log(f"{self.name}: WARNING: lock is already acquired on {self.path}")
      raise DeyeLockAlreadyAcquiredException(f"{type(self).__name__}: lock is already acquired on {self.path}")

    self.trim_file(self.log_filename, 1024 * 1024)

    self.lockfile = open(self.path, "a+")
    self.acquire_time = time.time()
    warning_printed = False
    self.timedout = False

    while True:
      try:
        # Try exclusive lock, non-blocking
        DeyeFileLock.flock(self.lockfile, DeyeFileLock.LOCK_EX | DeyeFileLock.LOCK_NB)
        if warning_printed:
          elapsed = time.time() - self.acquire_time
          self.log(f"{self.name}: acquired exclusive lock on {self.path} after {round(elapsed, 2)} sec")
        else:
          self.log(f"{self.name}: acquired exclusive lock on {self.path}")
        return
      except (BlockingIOError, PermissionError):
        if not warning_printed:
          self.log(f"{self.name}: lock is busy, waiting up to {timeout} seconds...")
          warning_printed = True

        elapsed = time.time() - self.acquire_time
        if elapsed >= timeout:
          self.log(f"{self.name}: timeout after {timeout} sec while waiting for lock on {self.path}")
          self.lockfile.close()
          self.lockfile = None
          self.timedout = True
          raise DeyeLockTimeoutException(
            f"{type(self).__name__}: timeout after {timeout} sec while waiting for lock on {self.path}")
        # wait before retrying
        time.sleep(random.uniform(0.15, 0.3))

  def release(self) -> None:
    """
    Release the acquired lock and close the file.
    Logs the elapsed time the lock was held.
    """
    if self.lockfile is not None:
      DeyeFileLock.flock(self.lockfile, DeyeFileLock.LOCK_UN)
      self.lockfile.close()
      self.lockfile = None
      elapsed = time.time() - self.acquire_time
      self.log(f"{self.name}: released lock on {self.path} after {round(elapsed, 2)} sec")
    elif not self.timedout:
      self.log(f"{self.name}: WARNING: tried to release lock on {self.path}, but no lock was held")
      raise DeyeLockNotHeldException(
        f"{type(self).__name__}: tried to release lock on {self.path}, but no lock was held")
