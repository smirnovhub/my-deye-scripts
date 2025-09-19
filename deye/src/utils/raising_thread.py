import threading

class RaisingThread(threading.Thread):
  """
  A custom Thread subclass that captures exceptions raised during
  the thread's execution and re-raises them when join() is called.

  This ensures that errors in background threads are not silently
  ignored and can be handled in the main thread.

  """

  # Override the standard run() method of threading.Thread
  # This method is executed when the thread starts
  def run(self):
    # Store any exception that occurs inside the thread
    self._exc = None
    try:
      # Call the parent class's run() method,
      # which will execute the target function provided at thread creation
      super().run()
    except Exception as e:
      # If an exception occurs in the thread,
      # capture and save it instead of letting it be swallowed silently
      self._exc = e

  # Override the join() method so that exceptions from the thread
  # are propagated back to the caller
  def join(self, timeout = None):
    # Wait for the thread to finish, respecting an optional timeout
    super().join(timeout = timeout)

    # If an exception was stored during run(),
    # raise it here in the main thread context
    # This makes thread behavior more predictable,
    # since errors in background threads are often invisible by default
    if self._exc:
      raise self._exc
