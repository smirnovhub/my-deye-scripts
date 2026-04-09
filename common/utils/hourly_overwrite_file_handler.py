import logging
import threading

from hourly_log_rotator import HourlyLogRotator

class HourlyOverwriteFileHandler(logging.Handler):
  def __init__(
    self,
    directory: str,
    log_file_template: str,
    encoding: str = "utf-8",
  ):
    super().__init__()
    self._rotator = HourlyLogRotator(
      directory = directory,
      log_file_template = log_file_template,
      encoding = encoding,
    )

    self._lock = threading.RLock()

    with self._lock:
      self._rotator.open_initial_stream()

  def emit(self, record: logging.LogRecord):
    try:
      with self._lock:
        self._rotator.rollover_if_needed()
        msg = self.format(record)
        self._rotator.write(msg)
    except Exception:
      self.handleError(record)

  def close(self):
    with self._lock:
      self._rotator.close()
    super().close()
