import os
import time
import logging

from typing import Dict
from pathlib import Path
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_csv_utils import DeyeCsvUtils
from deye_registers import DeyeRegisters
from deye_file_with_lock_async import DeyeFileWithLockAsync
from deye_registers_holder_async import DeyeRegistersHolderAsync
from data_collector_registers import DataCollectorRegisters
from data_collector_config import DataCollectorConfig

class DataCollector:
  def __init__(self, config: DataCollectorConfig):
    self._loggers = DeyeLoggers()
    self._data_path = f"data/{config.DEYE_DATA_COLLECTOR_DIR}"

    data_dir = Path(self._data_path)
    data_dir.mkdir(parents = True, exist_ok = True)

  def _get_thresholds(self) -> Dict[str, float]:
    registers = DeyeRegisters()
    return {
      registers.gen_power_register.description: 7.0,
      registers.pv1_current_register.description: 0.2,
      registers.pv1_power_register.description: 15.0,
      registers.pv1_voltage_register.description: 50.0,
      registers.pv2_current_register.description: 0.2,
      registers.pv2_power_register.description: 15.0,
      registers.pv2_voltage_register.description: 50.0,
      registers.pv_total_current_register.description: 0.2,
      registers.pv_total_power_register.description: 30.0,
    }

  async def main_logic(self, config: DataCollectorConfig, logger: logging.Logger) -> None:
    holder = await self._read_registers(self._loggers, logger)

    current_date = datetime.now().strftime("%Y-%m-%d")
    data_file_path = os.path.join(self._data_path, f"{current_date}.csv")

    data_dir = Path(data_file_path)

    write_header = not os.path.exists(data_file_path) or os.path.getsize(data_file_path) == 0

    if write_header:
      self._remove_old_files(
        directory = data_dir,
        days_threshold = config.DATA_RETENTION_DAYS,
        logger = logger,
      )

    header = DeyeCsvUtils.get_csv_header()
    lines = DeyeCsvUtils.get_csv_lines(
      holder = holder,
      loggers = self._loggers,
    )

    lines_to_write = "\n".join(lines)

    async with DeyeFileWithLockAsync(path = data_file_path, mode = "a") as f:
      if write_header:
        f.write(header)

      f.write(f"{lines_to_write}\n")
      f.flush()

    logger.info("-------------------------------------")

  async def save_thresholds(self, logger: logging.Logger) -> None:
    logger.info("Saving thresholds...")

    thresholds = self._get_thresholds()
    thresholds_str = "\n".join([f"{key},{value}" for key, value in thresholds.items()])

    thresholds_file_path = os.path.join(self._data_path, "thresholds.csv")

    # Write thresholds
    async with DeyeFileWithLockAsync(path = thresholds_file_path, mode = "w") as f:
      f.write("register,threshold\n")
      f.write(thresholds_str)
      f.flush()

    logger.info("Thresholds saved.")

  async def _read_registers(
    self,
    loggers: DeyeLoggers,
    logger: logging.Logger,
  ) -> DeyeRegistersHolderAsync:
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
    self,
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
