import os
import time
import logging

from typing import Dict
from pathlib import Path
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_csv_utils import DeyeCsvUtils
from deye_file_with_lock_async import DeyeFileWithLockAsync
from deye_registers_holder_async import DeyeRegistersHolderAsync
from data_collector_registers import DataCollectorRegisters
from data_collector_config import DataCollectorConfig

DATA_PATH = "data/deye-collected-data"

def _get_thresholds(holder: DeyeRegistersHolderAsync) -> Dict[str, float]:
  return {
    holder.master_registers.gen_power_register.description: 7.0,
    holder.master_registers.pv1_current_register.description: 0.2,
    holder.master_registers.pv1_power_register.description: 15.0,
    holder.master_registers.pv1_voltage_register.description: 50.0,
    holder.master_registers.pv2_current_register.description: 0.2,
    holder.master_registers.pv2_power_register.description: 15.0,
    holder.master_registers.pv2_voltage_register.description: 50.0,
    holder.master_registers.pv_total_current_register.description: 0.2,
    holder.master_registers.pv_total_power_register.description: 30.0,
  }

async def main_logic(config: DataCollectorConfig, logger: logging.Logger) -> None:
  loggers = DeyeLoggers()

  holder = await _read_registers(loggers, logger)

  now = datetime.now()

  current_date = now.strftime("%Y-%m-%d")

  data_file_path = os.path.join(DATA_PATH, f"{current_date}.csv")

  data_dir = Path(data_file_path)
  data_dir.parent.mkdir(parents = True, exist_ok = True)

  write_header = not os.path.exists(data_file_path) or os.path.getsize(data_file_path) == 0

  if write_header:
    _remove_old_files(
      directory = data_dir,
      days_threshold = config.DATA_RETENTION_DAYS,
      logger = logger,
    )

  header = DeyeCsvUtils.get_csv_header()
  lines = DeyeCsvUtils.get_csv_lines(
    holder = holder,
    loggers = loggers,
  )

  lines_to_write = "\n".join(lines)

  async with DeyeFileWithLockAsync(data_file_path, "a", encoding = "utf-8") as f:
    if write_header:
      f.write(header)

    f.write(f"{lines_to_write}\n")
    f.flush()

  thresholds = _get_thresholds(holder)
  thresholds_str = "\n".join([f"{key},{value}" for key, value in thresholds.items()])

  thresholds_file_path = os.path.join(DATA_PATH, "thresholds.csv")

  # Write thresholds
  async with DeyeFileWithLockAsync(thresholds_file_path, "w", encoding = "utf-8") as f:
    f.write("parameter,threshold\n")
    f.write(thresholds_str)
    f.flush()

  logger.info("-------------------------------------")

  raise RuntimeError("TEST")

async def _read_registers(loggers: DeyeLoggers, logger: logging.Logger) -> DeyeRegistersHolderAsync:
  retry_attempts = 5
  retry_delay_sec = 6
  last_exception = None

  for attempt in range(retry_attempts):
    holder = DeyeRegistersHolderAsync(
      loggers = loggers.loggers,
      register_creator = lambda prefix: DataCollectorRegisters(prefix),
      name = 'data_collector',
      socket_timeout = 7,
      verbose = False,
    )

    try:
      logger.info("Reading registers...")
      await holder.read_registers()
      logger.info("Registers read successful.")
      return holder
    except Exception as e:
      last_exception = e
      logger.error(f"An exception occurred: {e}. Retrying...")
    finally:
      holder.disconnect()

    if attempt < retry_attempts - 1:
      time.sleep(retry_delay_sec)

  # Raise exception if all attempts failed
  if last_exception:
    logger.error("All retry attempts were unsuccessful.")
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
