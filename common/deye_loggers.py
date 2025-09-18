from typing import List, Union
from deye_logger import DeyeLogger
from deye_system_type import DeyeSystemType

class DeyeLoggers:
  def __init__(self):
    self._master_logger = DeyeLogger(
      name = 'master',
      ip = '192.168.0.73',
      serial = 1234567890,
    )
    self._loggers = [
      self._master_logger,
#      DeyeLogger(
#        name = 'slave1',
#        ip = '192.168.0.75',
#        serial = 1234567890,
#      ),
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

  @property
  def system_type(self) -> DeyeSystemType:
    return DeyeSystemType.multi_inverter if self.count > 1 else DeyeSystemType.single_inverter

  def get_logger_by_name(self, name: str) -> Union[DeyeLogger, None]:
    for logger in self._loggers:
      if logger.name == name:
        return logger
    return None
