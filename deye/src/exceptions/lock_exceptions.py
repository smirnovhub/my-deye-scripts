from deye_exceptions import DeyeKnownException

class DeyeFileLockingException(DeyeKnownException):
  """
  Base exception for errors related to file locking in DeyeFileLocker.

  This exception is raised when a file lock cannot be acquired or released properly.
  For example, it is raised if the lock file remains busy for the entire duration
  of the `timeout` parameter in `DeyeFileLocker.acquire()`.
  """
  pass

class DeyeLockTimeoutException(DeyeFileLockingException):
  """
  Raised when acquiring a file lock times out in DeyeFileLocker.

  This exception indicates that the lock could not be obtained within the 
  specified `timeout` period in `DeyeFileLocker.acquire()`.
  """
  pass

class DeyeLockAlreadyAcquiredException(DeyeFileLockingException):
  """
  Raised when attempting to acquire a lock on a file that is already locked by the same
  process or context.

  Indicates that the file is already locked and cannot be re-acquired until it is released.
  """
  pass

class DeyeLockNotHeldException(DeyeFileLockingException):
  """
  Raised when attempting to release a file lock that is not currently held.

  Indicates that no lock exists for the file, so releasing it is invalid.
  """
  pass
