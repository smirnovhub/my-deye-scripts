import traceback

class DeyeException(Exception):
  """Base class for all exceptions in the Deye apps"""
  def __init__(self, message: str = "", stacktrace: str = ""):
    """
    Initialize the exception with an optional message and stacktrace.

    Args:
        message (str): Human-readable description of the error.
        stacktrace (str): String representation of the stacktrace,
                          useful for debugging/logging.
    """
    super().__init__(message)

    # If stacktrace not provided, try to capture automatically
    if stacktrace:
      self.stacktrace: str = stacktrace
    else:
      # format_exc() returns "NoneType: None\n" if called outside of an exception handler
      trace = traceback.format_exc()
      self.stacktrace: str = trace.strip()

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

class DeyeConnectionErrorException(DeyeKnownException):
  """Raised when connection error"""
  pass

class DeyeQueueIsEmptyException(DeyeKnownException):
  """
  Raised when Queue.get() fails because the queue is empty
  and no item could be retrieved before the timeout expired
  """
  pass
