from typing import List
from deye_logger import DeyeLogger

class DeyeLoggers:
  def __init__(self):
    self._master_logger = DeyeLogger(name = 'master', ip = '192.168.0.73', serial = 1234567890)
    self._loggers = [
      self._master_logger,
#      DeyeLogger(name = 'slave1', ip = '192.168.0.75', serial = 1234567890)
    ]

  @property
  def master(self) -> DeyeLogger:
    return self._master_logger

  @property
  def loggers(self) -> List[DeyeLogger]:
    return self._loggers.copy()

  @property
  def count(self) -> int:
    return len(self._loggers)

  def get_logger_by_name(self, name: str) -> DeyeLogger:
    for logger in self._loggers:
      if logger.name == name:
        return logger
    return None
