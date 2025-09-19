import io
import os
import time

from deye_exceptions import DeyeFileLockingException

from deye_file_lock import (
  flock,
  LOCK_SH,
  LOCK_EX,
  LOCK_NB,
  LOCK_UN,
)

class DeyeFileWithLock:
  """
  Provides a context for safely accessing files with advisory locks.

  This class ensures that files are locked correctly for reading or writing
  on Unix-like systems using `fcntl`. It supports both shared (read) and
  exclusive (write) locks, with optional retry logic and timeout handling.

  Parameters:
      verbose (bool, optional): If True, prints lock acquisition/release
                                messages to the console. Defaults to False.

  Features:
      - Acquire exclusive or shared locks with automatic retries.
      - Open files in read, write, or append modes while holding appropriate locks.
      - Release locks automatically when closing the file.
      - Raise `DeyeFileLockingException` if a lock cannot be acquired within the timeout.
  """
  def __init__(self, verbose: bool = False):
    self.sfile: io.IOBase = None
    self.path: str = None
    self.lock_name: str = None
    self.verbose: bool = verbose

  def _acquire_lock_with_retry(self, file_obj: io.IOBase, lock_type: int, timeout: int = 15) -> None:
    """
    Acquire a file lock with retries up to the specified timeout.

    Args:
        file_obj (IOBase): Open file object to lock.
        lock_type (int): Lock type, either fcntl.LOCK_SH (shared) or fcntl.LOCK_EX (exclusive).
        timeout (int, optional): Maximum time in seconds to wait for lock acquisition. Defaults to 15.

    Raises:
        DeyeFileLockingException: If the lock cannot be acquired within the timeout.
    """
    start_time = time.time()
    warning_printed = False
    self.lock_name = "exclusive" if lock_type == LOCK_EX else "shared"

    while True:
      try:
        flock(file_obj, lock_type | LOCK_NB)
        if self.verbose:
          elapsed = round(time.time() - start_time, 1)
          if warning_printed:
            print(f"Acquired {self.lock_name} lock on {self.path} after {elapsed} sec")
          else:
            print(f"Acquired {self.lock_name} lock on {self.path}")
        return
      except BlockingIOError:
        if self.verbose and not warning_printed:
          print(f"{self.lock_name} lock is busy, waiting up to {timeout} seconds...")
          warning_printed = True
        if time.time() - start_time >= timeout:
          if self.verbose:
            print(f"{self.lock_name}: timeout while waiting for lock on {self.path}")
          if self.sfile:
            self.sfile.close()
            self.sfile = None
          raise DeyeFileLockingException(f"{self.lock_name}: Timeout while waiting for lock on {self.path}")
        time.sleep(0.25)

  def open_file(self, path: str, mode: str, timeout: int = 15) -> io.IOBase:
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
    self.path = path

    if "w" in mode or "a" in mode:
      # Write/append mode: open file for read/write (a+) and lock exclusively
      self.sfile = open(path, "a+")
      self._acquire_lock_with_retry(self.sfile, LOCK_EX, timeout)

      # Position file pointer according to mode
      if "w" in mode:
        self.sfile.seek(0)
        self.sfile.truncate(0) # Truncate file after acquiring lock
      elif "a" in mode:
        self.sfile.seek(0, os.SEEK_END) # Move pointer to end for append
    else:
      # Read or read/write without explicit write intent: shared lock
      self.sfile = open(path, mode)
      self._acquire_lock_with_retry(self.sfile, LOCK_SH, timeout)

    return self.sfile

  def close_file(self) -> None:
    """
    Release the lock and close the file if it is open.

    Prints verbose messages if enabled.
    """
    if self.sfile:
      flock(self.sfile, LOCK_UN)
      self.sfile.close()
      self.sfile = None
      if self.verbose:
        print(f"Released {self.lock_name} lock on {self.path}")
