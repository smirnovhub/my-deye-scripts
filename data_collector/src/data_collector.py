import logging

from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from data_collector_registers import DataCollectorRegisters

# Main logic
def main_logic(data_dir: str, logger: logging.Logger) -> None:
  logger.info(datetime.isoformat())
  return

  loggers = DeyeLoggers()
  holder = DeyeRegistersHolder(
    loggers = loggers.loggers,
    register_creator = lambda prefix: DataCollectorRegisters(prefix),
    name = 'data_collector',
    socket_timeout = 7,
    verbose = False,
  )

  try:
    holder.read_registers()
  finally:
    holder.disconnect()
