import os

from typing import IO, Any

# Define flags compatible with fcntl
LOCK_EX = 0x1 # Exclusive lock
LOCK_SH = 0x2 # Shared lock
LOCK_NB = 0x4 # Non-blocking
LOCK_UN = 0x8 # Unlock

inverter_lock_file_name = 'inverter.lock'

if os.name == 'nt':
  import msvcrt
  import tempfile

  # Path to a temporary lock file used for Windows file locking.
  # Stored in the system's temporary directory.
  lock_path = os.path.join(tempfile.gettempdir(), 'deye')

  def flock(file: IO[Any], flags: int):
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
    if flags & LOCK_UN:
      # Unlock the file
      file.seek(0)
      msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, length)
    else:
      # Lock the file
      mode = msvcrt.LK_LOCK # Default blocking lock
      if flags & LOCK_NB:
        mode = msvcrt.LK_NBLCK # Non-blocking lock
      file.seek(0)
      msvcrt.locking(file.fileno(), mode, length)

else:
  import fcntl

  # Path to the lock file used on Unix-like systems.
  # NEED TO SET CORRECT RIGHTS FOR /var/lock:
  # chmod 1777 /var/lock
  lock_path = '/var/lock/deye'

  def flock(file: IO[Any], flags: int):
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
    if flags & LOCK_EX:
      fcntl_flags |= fcntl.LOCK_EX # type: ignore
    if flags & LOCK_SH:
      fcntl_flags |= fcntl.LOCK_SH # type: ignore
    if flags & LOCK_NB:
      fcntl_flags |= fcntl.LOCK_NB # type: ignore
    if flags & LOCK_UN:
      fcntl_flags = fcntl.LOCK_UN # type: ignore

    # Perform the actual file locking
    fcntl.flock(file.fileno(), fcntl_flags) # type: ignore
