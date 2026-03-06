from typing import List

from env_utils import EnvUtils
from deye_logger import DeyeLogger
from deye_base_loggers import DeyeBaseLoggers
from simple_singleton import singleton

@singleton
class DeyeLoggers(DeyeBaseLoggers):
  @property
  def master(self) -> DeyeLogger:
    return DeyeLogger(
      name = 'master',
      address = EnvUtils.get_master_logger_host(),
      serial = EnvUtils.get_master_logger_serial(),
      port = EnvUtils.get_master_logger_port(),
    )

  @property
  def slaves(self) -> List[DeyeLogger]:
    slaves = []

    # Iterate to find all configured slaves
    for i in range(1, 16):
      address = EnvUtils.get_slave_logger_host(i)

      # Stop the loop if the current slave address is empty or not set
      if not address:
        break

      # Append the slave logger if validation passes
      slaves.append(
        DeyeLogger(
          name = f'slave{i}',
          address = address,
          serial = EnvUtils.get_slave_logger_serial(i),
          port = EnvUtils.get_slave_logger_port(i),
        ))

    return slaves

  @property
  def remote_cache_server(self) -> str:
    return EnvUtils.get_remote_cache_server_url()
