import time
import logging

class DebugTimer:
  """
  Timer for measuring execution time of a code block.

  Example:
      from debug_timer import DebugTimer

      with DebugTimer("loading data"):
          load_data()

  Attributes:
      _title (str): Title describing the measured code section.

  Enable logging:
      logging.basicConfig(
        filename = '/tmp/deyeweb.log',
        filemode = 'w',
        level = logging.INFO,
        format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
        datefmt = DeyeUtils.time_format_str,
      )
  """
  def __init__(self, title: str):
    """
    Initialize the timer with a descriptive title.

    Args:
        title (str): Name shown in the final elapsed time message.
    """
    self._title = title

  def __enter__(self):
    self._start = time.perf_counter()
    return self

  def __exit__(self, *args):
    elapsed = time.perf_counter() - self._start
    self.print_message(f"Elapsed {self._title}: {elapsed:.3f} sec")

  def print_message(self, message: str):
    print(message)

class DebugTimerWithLog(DebugTimer):
  """
  Same as DebugTimer, but writes the output into the logging system.

  Example:
      import logging
      logging.basicConfig(level=logging.INFO)

      with DebugTimerWithLog("processing"):
          process_items()
  """
  def __init__(self, title: str):
    """
    Initialize the timer with a title and a logger instance.

    Args:
        title (str): Name shown in the final elapsed time log entry.
    """
    super().__init__(title)
    self._log = logging.getLogger()

  def print_message(self, message: str):
    self._log.info(message)
