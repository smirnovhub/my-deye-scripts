from typing import List, Optional

from deye_logger import DeyeLogger
from deye_system_type import DeyeSystemType
from deye_exceptions import DeyeNotImplementedException

class DeyeBaseLoggers:
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
