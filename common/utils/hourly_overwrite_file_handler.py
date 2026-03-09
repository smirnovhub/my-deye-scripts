import os
import logging
import threading

from typing import IO, Any, Optional
from datetime import datetime, date

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

    # Track both hour and date to handle inactivity > 24h
    self._current_hour: Optional[str] = None
    self._current_date: Optional[date] = None

    self._stream: Optional[IO[Any]] = None
    self._lock = threading.RLock()

    os.makedirs(self.directory, exist_ok = True)
    self._open_initial_stream()

  def _get_hour(self) -> str:
    return datetime.now().strftime("%H")

  def _get_date(self) -> date:
    return datetime.now().date()

  def _build_filename(self, hour: str) -> str:
    filename = self.log_file_template.format(hour)
    return os.path.join(self.directory, filename)

  def _open_initial_stream(self) -> None:
    """Initial startup: determine whether to append or overwrite."""
    current_date = self._get_date()
    current_hour = self._get_hour()

    filename = self._build_filename(current_hour)
    mode = "w" if self._is_file_too_old(filename, current_date) else "a"

    with self._lock:
      self._stream = open(filename, mode = mode, encoding = self.encoding)
      self._current_date = current_date
      self._current_hour = current_hour

  def _is_file_too_old(self, filename: str, current_date: date) -> bool:
    if not os.path.exists(filename):
      return False

    mtime = os.path.getmtime(filename)
    file_date = datetime.fromtimestamp(mtime).date()

    return file_date < current_date

  def _rollover_if_needed(self) -> None:
    """Check for hour change OR date change."""
    current_date = self._get_date()
    current_hour = self._get_hour()

    filename = self._build_filename(current_hour)
    too_old = self._is_file_too_old(filename, current_date)

    # Trigger rollover if the hour is different OR if it's a new day
    if too_old or current_hour != self._current_hour or current_date != self._current_date:
      with self._lock:
        if self._stream:
          self._stream.close()

        # Always overwrite when shifting to a new time slot
        mode = "w" if too_old else "a"
        self._stream = open(filename, mode = mode, encoding = self.encoding)
        self._current_date = current_date
        self._current_hour = current_hour

  def emit(self, record: logging.LogRecord):
    try:
      with self._lock:
        self._rollover_if_needed()

        if self._stream:
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
