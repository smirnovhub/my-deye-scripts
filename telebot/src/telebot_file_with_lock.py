import io
from deye_file_locker import DeyeFileLocker
from scheduler_constants import SchedulerConstants

class TelebotFileWithLock:
  """
  A helper class for working with files in a thread/process-safe way.
  It uses a global lock to prevent race conditions between the cron scheduler
  and telebot commands that may try to access the same file simultaneously.
  """
  def __init__(self, verbose = False):
    """
    Initialize the TelebotFileWithLock.

    Args:
        verbose (bool): If True, enables verbose logging in the DeyeFileLocker.
    """
    self.sfile: io.TextIOWrapper = None
    # Use global lock for all files to avoid conflicts with cron scheduler and telebot commands
    self.locker = DeyeFileLocker('telebot', SchedulerConstants.lock_file_name, verbose = verbose)

  def open_file(self, path, mode) -> io.TextIOWrapper:
    """
    Open a file with the given path and mode while ensuring exclusive access.

    The method acquires the global lock before opening the file,
    and then releases the lock immediately after opening to allow
    other processes to proceed.

    Args:
        path (str): The path to the file.
        mode (str): The mode in which the file should be opened (e.g., 'r', 'w', 'a').

    Returns:
        io.TextIOWrapper: The opened file object.
    """
    self.locker.acquire()
    try:
      self.sfile = open(path, mode)
    finally:
      self.locker.release()
    return self.sfile

  def close_file(self):
    """
    Close the currently opened file and release the global lock.

    Ensures that the file is properly closed and the lock is released
    even if an error occurs during closing.
    """
    try:
      if self.sfile:
        self.sfile.close()
        self.sfile = None
    finally:
      self.locker.release()
