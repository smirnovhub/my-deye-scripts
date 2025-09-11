import os

# Define flags compatible with fcntl
LOCK_EX = 0x1 # Exclusive lock
LOCK_SH = 0x2 # Shared lock
LOCK_NB = 0x4 # Non-blocking
LOCK_UN = 0x8 # Unlock

if os.name == 'nt':
  import msvcrt
  import tempfile

  lock_path = os.path.join(tempfile.gettempdir(), 'deye')

  # Cross-platform flock implementation for Windows.
  # :param file: Open file object
  # :param flags: Combination of LOCK_EX, LOCK_SH, LOCK_NB, LOCK_UN
  def flock(file, flags):
    length = 1  # Windows locking requires a length; we lock at least 1 byte
    if flags & LOCK_UN:
      # Unlock the file
      file.seek(0)
      msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, length)
    else:
      # Lock the file
      mode = msvcrt.LK_LOCK  # Default blocking lock
      if flags & LOCK_NB:
        mode = msvcrt.LK_NBLCK  # Non-blocking lock
      file.seek(0)
      msvcrt.locking(file.fileno(), mode, length)

else:
  import fcntl

  # NEED TO SET CORRECT RIGHTS FOR /var/lock:
  # chmod 1777 /var/lock
  lock_path = '/var/lock/deye'

  # Cross-platform flock implementation for Unix (Linux/macOS).
  # :param file: Open file object
  # :param flags: Combination of LOCK_EX, LOCK_SH, LOCK_NB, LOCK_UN
  def flock(file, flags):
    fcntl_flags = 0
    if flags & LOCK_EX:
      fcntl_flags |= fcntl.LOCK_EX
    if flags & LOCK_SH:
      fcntl_flags |= fcntl.LOCK_SH
    if flags & LOCK_NB:
      fcntl_flags |= fcntl.LOCK_NB
    if flags & LOCK_UN:
      fcntl_flags = fcntl.LOCK_UN
    # Perform the actual file locking
    fcntl.flock(file.fileno(), fcntl_flags)
