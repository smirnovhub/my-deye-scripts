#!/usr/bin/env python3

import os
import sys
import pathlib
import signal

from typing import IO, Any, Optional
from datetime import datetime, date

class HourlyLogRotator:
  """
  Stream-based hourly log rotator.

  Reads lines from stdin and writes them to files based on the current hour.
  If the existing file belongs to a previous day, it will be overwritten.
  """
  def __init__(
    self,
    directory: str,
    log_file_template: str,
    encoding: str = "utf-8",
  ):
    self._directory = directory
    self._log_file_template = log_file_template
    self._encoding = encoding

    self._stream: Optional[IO[Any]] = None
    self._current_hour: Optional[str] = None
    self._current_date: Optional[date] = None

    os.makedirs(self._directory, exist_ok = True)

  def open_initial_stream(self) -> None:
    """Initial startup: determine whether to append or overwrite."""
    current_date = self._get_date()
    current_hour = self._get_hour()

    filename = self._build_filename(current_hour)
    mode = "w" if self._is_file_too_old(filename, current_date) else "a"

    self._stream = open(filename, mode = mode, encoding = self._encoding)
    self._current_date = current_date
    self._current_hour = current_hour

  def rollover_if_needed(self) -> None:
    """Check for hour change OR date change."""
    current_date = self._get_date()
    current_hour = self._get_hour()

    filename = self._build_filename(current_hour)
    too_old = self._is_file_too_old(filename, current_date)

    # Trigger rollover if the hour is different OR if it's a new day
    if too_old or current_hour != self._current_hour or current_date != self._current_date:
      if self._stream:
        self._stream.close()

      # Always overwrite when shifting to a new time slot
      mode = "w" if too_old else "a"
      self._stream = open(filename, mode = mode, encoding = self._encoding)
      self._current_date = current_date
      self._current_hour = current_hour

  def write(self, msg: str) -> None:
    if self._stream:
      self._stream.write(msg + "\n")
      self._stream.flush()

  def run(self) -> None:
    self.open_initial_stream()

    for line in sys.stdin:
      self.rollover_if_needed()

      if self._stream:
        self._stream.write(line)
        self._stream.flush()

  def close(self) -> None:
    if self._stream:
      self._stream.close()
      self._stream = None

  def _get_hour(self) -> str:
    return datetime.now().strftime("%H")

  def _get_date(self) -> date:
    return datetime.now().date()

  def _build_filename(self, hour: str) -> str:
    return os.path.join(self._directory, self._log_file_template.format(hour))

  def _is_file_too_old(self, filename: str, current_date: date) -> bool:
    if not os.path.exists(filename):
      return False

    mtime = os.path.getmtime(filename)
    file_date = datetime.fromtimestamp(mtime).date()

    return file_date < current_date

def main() -> None:
  if len(sys.argv) != 3:
    script_name = pathlib.Path(__file__).name
    print(
      f"Usage: {script_name} <directory> <filename_template>",
      file = sys.stderr,
    )
    sys.exit(1)

  directory = sys.argv[1]
  template = sys.argv[2]

  rotator = HourlyLogRotator(directory, template)

  def shutdown(signum, frame):
    rotator.close()
    sys.exit(0)

  signal.signal(signal.SIGTERM, shutdown)
  signal.signal(signal.SIGINT, shutdown)

  try:
    rotator.run()
  finally:
    rotator.close()

if __name__ == "__main__":
  main()
