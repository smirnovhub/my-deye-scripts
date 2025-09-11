class DeyeException(Exception):
    """Base class for all exceptions in the Deye apps"""
    pass

class DeyeUnknownException(DeyeException):
    """Base class for unknown exceptions in the Deye apps"""
    pass

class DeyeKnownException(DeyeException):
    """Base class for known exceptions in the Deye apps"""
    pass

class DeyeNotImplementedException(DeyeKnownException):
    """
    Raised when a requested feature or method is not implemented
    """
    pass

class DeyeValueException(DeyeKnownException):
    """
    Raised when a function receives a value of an incorrect type
    or an invalid value that cannot be processed
    """
    pass

class DeyeNoSocketAvailableException(DeyeKnownException):
    """Raised when no socket is available for establishing a connection"""
    pass

class DeyeQueueIsEmptyException(DeyeKnownException):
    """
    Raised when Queue.get() fails because the queue is empty
    and no item could be retrieved before the timeout expired
    """
    pass

class DeyeFileLockingException(DeyeKnownException):
    """
    Raised when DeyeFileLocker fails to acquire an exclusive file lock.
    This exception indicates that the lock file remained busy during the entire
    waiting period defined by the `timeout` argument in `DeyeFileLocker.acquire()`.
    """
    pass

class DeyeEcoflowException(DeyeKnownException):
    """
    Raised when Ecoflow error occurred
    """
    pass
