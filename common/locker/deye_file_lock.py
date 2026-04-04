import asyncio
import os

from typing import IO, Any

class DeyeFileLock:
  # Define flags compatible with fcntl
  LOCK_EX = 0x1 # Exclusive lock
  LOCK_SH = 0x2 # Shared lock
  LOCK_NB = 0x4 # Non-blocking
  LOCK_UN = 0x8 # Unlock

  inverter_lock_file_name_template = 'inverter{0}.lock'

  @staticmethod
  async def flock_async(
    file: IO[Any],
    flags: int,
    retry_interval: float = 0.1,
    timeout: float = 10.0,
  ) -> None:
    """
    Asynchronous version of flock using non-blocking mode and asyncio.sleep.
    
    Parameters:
        file: Open file object.
        flags: Combination of LOCK_EX, LOCK_SH, LOCK_NB, LOCK_UN.
        retry_interval: Time to wait between attempts in seconds.
        timeout: Maximum time to wait for the lock before raising TimeoutError.
    """
    # If it's an unlock operation, do it immediately (it's always non-blocking)
    if flags & DeyeFileLock.LOCK_UN:
      DeyeFileLock.flock(file, flags)
      return

    # Force Non-Blocking flag for the retry loop logic
    nb_flags = flags | DeyeFileLock.LOCK_NB

    loop = asyncio.get_running_loop()
    start_time = loop.time()

    while True:
      try:
        # Try to acquire the lock in non-blocking mode
        DeyeFileLock.flock(file, nb_flags)
        # Lock acquired successfully
        return
      except (OSError, IOError, PermissionError):
        # If the user explicitly asked for non-blocking WITHOUT retries
        if flags & DeyeFileLock.LOCK_NB:
          raise

        # Check for timeout
        if (loop.time() - start_time) >= timeout:
          raise TimeoutError(f"System was unable to acquire file lock within {timeout}s")

        # Wait and let other async tasks run
        await asyncio.sleep(retry_interval)

  if os.name == 'nt':
    import msvcrt
    import tempfile

    # Path to a temporary lock file used for Windows file locking.
    # Stored in the system's temporary directory.
    lock_path = os.path.join(tempfile.gettempdir(), 'deye')

    @staticmethod
    def flock(file: IO[Any], flags: int) -> None:
      """
      Cross-platform file lock implementation for Windows.

      Locks or unlocks a file using msvcrt.locking().

      Parameters:
          file (file object): An open file object to lock or unlock.
          flags (int): Combination of LOCK_EX, LOCK_SH, LOCK_NB, LOCK_UN.

      Behavior:
          - LOCK_EX: Acquire an exclusive lock.
          - LOCK_SH: Acquire a shared lock (ignored on Windows, treated as exclusive).
          - LOCK_NB: Acquire the lock in non-blocking mode.
          - LOCK_UN: Release the lock.
      """
      length = 1 # Windows locking requires a length; we lock at least 1 byte
      if flags & DeyeFileLock.LOCK_UN:
        # Unlock the file
        file.seek(0)
        DeyeFileLock.msvcrt.locking(file.fileno(), DeyeFileLock.msvcrt.LK_UNLCK, length) # type: ignore
      else:
        # Lock the file
        mode = DeyeFileLock.msvcrt.LK_LOCK # type: ignore
        if flags & DeyeFileLock.LOCK_NB:
          mode = DeyeFileLock.msvcrt.LK_NBLCK # type: ignore
        file.seek(0)
        DeyeFileLock.msvcrt.locking(file.fileno(), mode, length) # type: ignore

  else:
    import fcntl

    # Path to the lock file used on Unix-like systems.
    # NEED TO SET CORRECT RIGHTS FOR /var/lock:
    # chmod 1777 /var/lock
    lock_path = '/var/lock/deye'

    @staticmethod
    def flock(file: IO[Any], flags: int) -> None:
      """
      Cross-platform file lock implementation for Unix (Linux/macOS).

      Locks or unlocks a file using fcntl.flock().

      Parameters:
          file (file object): An open file object to lock or unlock.
          flags (int): Combination of LOCK_EX, LOCK_SH, LOCK_NB, LOCK_UN.

      Behavior:
          - LOCK_EX: Acquire an exclusive lock.
          - LOCK_SH: Acquire a shared lock.
          - LOCK_NB: Acquire the lock in non-blocking mode.
          - LOCK_UN: Release the lock.

      Notes:
          - fcntl.flock is advisory; processes must cooperate to respect locks.
          - The flags are combined according to the fcntl module.
      """
      fcntl_flags = 0
      if flags & DeyeFileLock.LOCK_EX:
        fcntl_flags |= DeyeFileLock.fcntl.LOCK_EX # type: ignore
      if flags & DeyeFileLock.LOCK_SH:
        fcntl_flags |= DeyeFileLock.fcntl.LOCK_SH # type: ignore
      if flags & DeyeFileLock.LOCK_NB:
        fcntl_flags |= DeyeFileLock.fcntl.LOCK_NB # type: ignore
      if flags & DeyeFileLock.LOCK_UN:
        fcntl_flags = DeyeFileLock.fcntl.LOCK_UN # type: ignore

      # Perform the actual file locking
      DeyeFileLock.fcntl.flock(file.fileno(), fcntl_flags) # type: ignore
