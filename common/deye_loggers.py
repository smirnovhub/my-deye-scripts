from typing import List

from deye_logger import DeyeLogger
from deye_base_loggers import DeyeBaseLoggers

class DeyeLoggers(DeyeBaseLoggers):
  @property
  def master(self) -> DeyeLogger:
    return DeyeLogger(
      name = 'master',
      address = '192.168.0.73',
      serial = 1234567890,
    )

  @property
  def slaves(self) -> List[DeyeLogger]:
    return [
      #DeyeLogger(
      #  name = 'slave1',
      #  address = '192.168.0.75',
      #  serial = 1234567890,
      #),
    ]

  @property
  def remote_cache_server(self) -> str:
    # Specify cache server if you want
    # to use remote cache, as example:
    # http://192.168.0.77/
    # See 'deyecache' folder for details
    return ''
