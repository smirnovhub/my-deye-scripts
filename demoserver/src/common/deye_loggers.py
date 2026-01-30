from typing import List

from deye_logger import DeyeLogger
from deye_base_loggers import DeyeBaseLoggers

class DeyeLoggers(DeyeBaseLoggers):
  @property
  def master(self) -> DeyeLogger:
    return DeyeLogger(
      name = 'master',
      address = DeyeBaseLoggers.demo_server_name,
      serial = 1,
      port = 5001,
    )

  @property
  def slaves(self) -> List[DeyeLogger]:
    count = 1
    return [
      DeyeLogger(
        name = f'slave{i}',
        address = DeyeBaseLoggers.demo_server_name,
        serial = self.master.serial + i,
        port = self.master.port + i,
      ) for i in range(1, count + 1)
    ]
