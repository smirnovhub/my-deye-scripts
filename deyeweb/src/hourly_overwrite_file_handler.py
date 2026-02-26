import os
import time
import logging
import threading

from datetime import datetime

class HourlyOverwriteFileHandler(logging.Handler):
  def __init__(
    self,
    directory: str,
    log_file_template: str,
    encoding: str = "utf-8",
  ):
    super().__init__()
    self.directory = directory
    self.log_file_template = log_file_template
    self.encoding = encoding
    self._current_hour = None
    self._stream = None
    self._lock = threading.RLock()

    os.makedirs(self.directory, exist_ok = True)
    self._open_initial_stream()

  def _get_hour(self) -> str:
    return datetime.now().strftime("%H")

  def _build_filename(self, hour: str) -> str:
    filename = self.log_file_template.format(hour)
    return os.path.join(self.directory, filename)

  def _open_initial_stream(self):
    """Open file at startup: overwrite if old, append if current day."""
    hour = self._get_hour()
    filename = self._build_filename(hour)

    mode = "a"
    if os.path.exists(filename):
      mtime = os.path.getmtime(filename)
      file_day = time.localtime(mtime).tm_mday
      if file_day != datetime.now().day:
        # File from yesterday - overwrite
        mode = "w"

    with self._lock:
      self._stream = open(filename, mode = mode, encoding = self.encoding)
      self._current_hour = hour

  def _rollover_if_needed(self):
    hour = self._get_hour()

    if hour != self._current_hour:
      with self._lock:
        if self._stream:
          self._stream.close()

        filename = self._build_filename(hour)

        # Overwrite only on real hour change
        self._stream = open(filename, mode = "w", encoding = self.encoding)

        self._current_hour = hour

  def emit(self, record: logging.LogRecord):
    try:
      with self._lock:
        self._rollover_if_needed()

        msg = self.format(record)
        self._stream.write(msg + "\n")
        self._stream.flush()

    except Exception:
      self.handleError(record)

  def close(self):
    with self._lock:
      if self._stream:
        self._stream.close()
        self._stream = None
    super().close()
