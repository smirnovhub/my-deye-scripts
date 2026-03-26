import os
import time
import logging

from pathlib import Path
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from data_collector_registers import DataCollectorRegisters
from deye_register_average_type import DeyeRegisterAverageType
from data_collector_config import DataCollectorConfig

# Main logic
def main_logic(config: DataCollectorConfig, logger: logging.Logger) -> None:
  loggers = DeyeLoggers()

  holder = _read_registers(loggers)

  now = datetime.now()

  current_date = now.strftime("%Y-%m-%d")
  timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

  data_file_path = f"data/deye-collected-data/{current_date}.csv"

  data_dir = Path(data_file_path)
  data_dir.parent.mkdir(parents = True, exist_ok = True)

  header = "timestamp,inverter,parameter,value,unit\n"

  write_header = not os.path.exists(data_file_path) or os.path.getsize(data_file_path) == 0

  if write_header:
    _remove_old_files(
      directory = data_dir,
      days_threshold = config.DATA_RETENTION_DAYS,
      logger = logger,
    )

  with open(data_file_path, "a", encoding = "utf-8") as f:
    if write_header:
      f.write(header)

    for inverter, registers in holder.all_registers.items():
      for register in registers.all_registers:
        is_accumulated = registers.prefix == loggers.accumulated_registers_prefix

        if is_accumulated and register.can_accumulate == False:
          continue

        is_slave = inverter != loggers.master.name
        is_only_master = register.avg_type == DeyeRegisterAverageType.only_master

        if is_slave and (register.can_write or is_only_master):
          continue

        f.write(f"{timestamp},{inverter},{register.description},{register.pretty_value},{register.suffix}\n")

    f.flush()

def _read_registers(loggers: DeyeLoggers) -> DeyeRegistersHolder:
  retry_attempts = 5
  retry_delay_sec = 6
  last_exception = None

  for attempt in range(retry_attempts):
    holder = DeyeRegistersHolder(
      loggers = loggers.loggers,
      register_creator = lambda prefix: DataCollectorRegisters(prefix),
      name = 'data_collector',
      socket_timeout = 7,
      verbose = False,
    )

    try:
      holder.read_registers()
      return holder

    except Exception as e:
      last_exception = e
    finally:
      holder.disconnect()

    if attempt < retry_attempts - 1:
      time.sleep(retry_delay_sec)

  # Raise exception if all attempts failed
  if last_exception:
    raise last_exception
  else:
    raise Exception("Unknown error")

def _remove_old_files(
  directory: Path,
  days_threshold: int,
  logger: logging.Logger,
):
  logger.info(f"Deleting old data files with age more than {days_threshold} days...")

  # Convert days to seconds for comparison
  seconds_threshold = days_threshold * 24 * 60 * 60
  current_time = time.time()

  # Iterate through all .csv files in the directory
  for file_path in directory.glob("*.csv"):
    try:
      # Get the last modification time
      file_mod_time = file_path.stat().st_mtime
      file_age_seconds = current_time - file_mod_time

      # Check if the file is older than the threshold
      if file_age_seconds > seconds_threshold:
        file_path.unlink()
        logger.info(f"Deleted: {file_path.name}")
    except Exception as e:
      # Handle potential errors during file access or deletion
      logger.error(f"Error removing {file_path.name}: {e}")
