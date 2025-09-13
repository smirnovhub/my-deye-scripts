import os
import time
import random

from deye_utils import *
from deye_file_lock import *
from datetime import datetime
from deye_exceptions import DeyeFileLockingException

# ---------------------------------------
# Class for handling exclusive file locks
# ---------------------------------------
class DeyeFileLocker:
  def __init__(self, name, path, verbose=False):
    self.name = name
    self.path = path
    self.verbose = verbose
    self.lockfile = None
    self.timedout = False

    # Ensure lock file exists
    ensure_dir_and_file_exists(path, dir_mode = 0o777, file_mode = 0o666)

    self.rnd = random.randint(1000000, 9999999)
    self.log_filename = f'{os.path.dirname(path)}/locker.log'

    ensure_dir_and_file_exists(self.log_filename, dir_mode = 0o777, file_mode = 0o666)

  def log(self, message):
    now = datetime.now()
    date = now.strftime('[%Y-%m-%d %H:%M:%S]')

    with open(self.log_filename, "a") as f:
      f.write(f'{date} [{self.rnd}] {message}\n')

    if self.verbose:
      print(message)

  def trim_file(self, filename, trim_size):
    # wait while file increased up to 20% and then trim
    max_size = int(trim_size * 1.2)
    file_size = os.path.getsize(filename)
    if file_size <= max_size:
      return  # trimming not needed
  
    with open(filename, "rb+") as f:
      try:
        # Try to acquire exclusive lock (non-blocking)
        flock(f, LOCK_EX | LOCK_NB)
      except BlockingIOError:
        # Someone else is working with file — do nothing
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
        flock(f, LOCK_UN)

  #  Acquire exclusive lock on the file.
  #  Waits up to 'timeout' seconds before giving up.
  #  Returns True if lock acquired, False if timeout.
  def acquire(self, timeout = 15):
    if self.lockfile is not None:
      self.log(f"{self.name}: WARNING: lock is already acquired on {self.path}")
      return

    self.trim_file(self.log_filename, 1024 * 1024)

    self.lockfile = open(self.path, "a+")
    self.acquire_time = time.time()
    warning_printed = False
    self.timedout = False

    while True:
      try:
        # Try exclusive lock, non-blocking
        flock(self.lockfile, LOCK_EX | LOCK_NB)
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
          raise DeyeFileLockingException(f"{self.name}: Timeout after {timeout} sec while waiting for lock on {self.path}")
        # wait before retrying
        time.sleep(random.uniform(0.15, 0.3))

  def release(self):
    # Release lock and close file
    if self.lockfile is not None:
      flock(self.lockfile, LOCK_UN)
      self.lockfile.close()
      self.lockfile = None
      elapsed = time.time() - self.acquire_time
      self.log(f"{self.name}: released lock on {self.path} after {round(elapsed, 2)} sec")
    elif not self.timedout:
      self.log(f"{self.name}: WARNING: tried to release lock on {self.path}, but no lock was held")
