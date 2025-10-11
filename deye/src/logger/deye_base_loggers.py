from typing import List, Optional

from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_system_type import DeyeSystemType
from deye_exceptions import DeyeNotImplementedException

class DeyeBaseLoggers:
  _instance = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      if DeyeUtils.is_tests_on():
        from deye_test_loggers import DeyeTestLoggers
        cls._instance = super().__new__(DeyeTestLoggers) # type: ignore
      else:
        cls._instance = super().__new__(cls) # type: ignore
    return cls._instance

  @property
  def master(self) -> DeyeLogger:
    raise DeyeNotImplementedException('master')

  @property
  def slaves(self) -> List[DeyeLogger]:
    raise DeyeNotImplementedException('slaves')

  @property
  def loggers(self) -> List[DeyeLogger]:
    return [self.master] + self.slaves

  @property
  def count(self) -> int:
    return len(self.loggers)

  @property
  def is_test_loggers(self) -> bool:
    for logger in self.loggers:
      if logger.address != '127.0.0.1':
        return False
    return True

  def get_logger_by_name(self, name: str) -> Optional[DeyeLogger]:
    for logger in self.loggers:
      if logger.name == name:
        return logger
    return None

  @property
  def system_type(self) -> DeyeSystemType:
    return DeyeSystemType.multi_inverter if self.count > 1 else DeyeSystemType.single_inverter

  @property
  def accumulated_registers_prefix(self) -> str:
    return 'all'
