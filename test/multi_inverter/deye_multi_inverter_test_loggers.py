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
      port = 8001,
    )

  @property
  def slaves(self) -> List[DeyeLogger]:
    return [
      DeyeLogger(
        name = 'slave1_inverter',
        address = '127.0.0.1',
        serial = 2,
        port = 8002,
      ),
      DeyeLogger(
        name = 'slave2_inverter',
        address = '127.0.0.1',
        serial = 3,
        port = 8003,
      ),
      DeyeLogger(
        name = 'slave3_inverter',
        address = '127.0.0.1',
        serial = 4,
        port = 8004,
      ),
    ]
