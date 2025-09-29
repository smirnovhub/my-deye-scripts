from typing import List

from deye_logger import DeyeLogger
from deye_base_loggers import DeyeBaseLoggers

class DeyeLoggers(DeyeBaseLoggers):
  @property
  def master(self) -> DeyeLogger:
    return DeyeLogger(
      name = 'master_inverter',
      address = '127.0.0.1',
      serial = 1,
      port = 7000,
    )

  @property
  def slaves(self) -> List[DeyeLogger]:
    return []
