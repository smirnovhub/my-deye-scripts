import os
import re
import time
import asyncio
import logging

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_csv_utils import DeyeCsvUtils
from deye_registers import DeyeRegisters
from deye_grid_state import DeyeGridState
from deye_file_with_lock_async import DeyeFileWithLockAsync
from deye_registers_holder_async import DeyeRegistersHolderAsync
from data_collector_registers import DataCollectorRegisters
from data_collector_config import DataCollectorConfig

class DataCollector:
  def __init__(self, config: DataCollectorConfig):
    self._loggers = DeyeLoggers()
    self._data_path = f"data/{config.DEYE_DATA_COLLECTOR_DIR}"
    self._data_retention_days = config.DATA_RETENTION_DAYS
    self._load_power_ratio_threshold = config.DEYE_DATA_COLLECTOR_LOAD_POWER_RATIO

    self._make_dirs(self._data_path)

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

  async def main_logic(self, logger: logging.Logger) -> None:
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")

    data_dir = os.path.join(self._data_path, f"{now.year}/{now.month:02d}")

    self._make_dirs(data_dir)
    self._chmod_dir(data_dir, 0o1777)

    data_file_path = os.path.join(data_dir, f"{current_date}.csv")

    write_header = not os.path.exists(data_file_path) or os.path.getsize(data_file_path) == 0

    if write_header:
      self._remove_old_files(
        directory = Path(self._data_path),
        days_threshold = self._data_retention_days,
        logger = logger,
      )

    holder = await self._read_registers(self._load_power_ratio_threshold, logger)

    lines = DeyeCsvUtils.get_csv_lines(
      holder = holder,
      loggers = self._loggers,
    )

    lines_to_write = "\n".join(lines)

    async with DeyeFileWithLockAsync(path = data_file_path, mode = "a") as f:
      if write_header:
        header = DeyeCsvUtils.get_csv_header()
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
    load_power_ratio_threshold: float,
    logger: logging.Logger,
  ) -> DeyeRegistersHolderAsync:
    best_ratio = -1.0
    retry_attempts = 5
    retry_delay_sec = 7
    best_holder: Optional[DeyeRegistersHolderAsync] = None
    last_exception: Any = None

    logger.info(f'Load power ratio threshold: {load_power_ratio_threshold}')

    for attempt in range(1, retry_attempts + 1):
      if attempt > 1:
        await asyncio.sleep(retry_delay_sec)

      holder = DeyeRegistersHolderAsync(
        loggers = self._loggers.loggers,
        register_creator = lambda prefix: DataCollectorRegisters(prefix),
        name = 'data_collector',
        socket_timeout = 7,
        verbose = False,
      )

      last_exception = None

      try:
        await holder.read_registers()
      except Exception as e:
        last_exception = e
        logger.error(f'An exception occurred: {e}. Retrying attempt {attempt}/{retry_attempts}...')
        continue
      finally:
        holder.disconnect()

      if self._loggers.count == 1:
        return holder

      load_powers: List[int] = []
      for _, registers in holder.all_registers.items():
        if registers.prefix != self._loggers.accumulated_registers_prefix:
          load_powers.append(registers.load_power_register.value)

      load_power_ratio = self._get_ratio(load_powers)

      if holder.accumulated_registers.grid_state_register.value == DeyeGridState.off_grid:
        logger.warning(f'Grid state is off-grid. Skip load power ratio checking')
        logger.info(f'Load power ratio: {load_power_ratio:.5f}')
        return holder

      if load_power_ratio > load_power_ratio_threshold:
        logger.info(f'Load power ratio is ok: {load_power_ratio:.5f}')
        return holder

      if load_power_ratio > best_ratio:
        best_ratio = load_power_ratio
        best_holder = holder
        logger.info(f'Got holder with ratio: {load_power_ratio:.5f}')

      logger.warning(f'Load power ratio is wrong: {load_power_ratio:.5f}. '
                     f'Attempt {attempt}/{retry_attempts}. '
                     f'Retrying in {retry_delay_sec} seconds...')
    else:
      # Executed only if all attempts are exhausted
      logger.warning(f'Load power ratio is still wrong ({best_ratio:.5f}) '
                     f'after {retry_attempts} attempts.')

      if best_holder:
        return best_holder

      if last_exception:
        raise last_exception

      raise RuntimeError("Can't read deye registers.")

  def _get_ratio(self, values: List[int]) -> float:
    if not values:
      return 0

    # Find the smallest and largest values in the set
    min_val = min(values)
    max_val = max(values)

    # Avoid division by zero if necessary
    if max_val == 0:
      return 0

    # Calculate the ratio of the smallest to the largest
    return min_val / max_val

  def _remove_old_files(
    self,
    directory: Path,
    days_threshold: int,
    logger: logging.Logger,
  ) -> None:
    logger.info(f"Deleting old data files with age more than {days_threshold} days...")

    # Convert days to seconds for comparison
    seconds_threshold = days_threshold * 24 * 60 * 60
    current_time = time.time()

    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\.csv$")

    # Use rglob for recursive directory traversal
    for file_path in directory.rglob("*.csv"):
      if not pattern.match(file_path.name):
        continue

      try:
        # Get the last modification time
        file_mod_time = file_path.stat().st_mtime
        file_age_seconds = current_time - file_mod_time

        # Check if the file is older than the threshold
        if file_age_seconds > seconds_threshold:
          file_path.unlink()
          logger.info(f"Deleted: {file_path}")
      except Exception as e:
        # Handle potential errors during file access or deletion
        logger.error(f"Error removing {file_path}: {e}")

  def _make_dirs(self, path: str) -> None:
    dir = Path(path)
    dir.mkdir(parents = True, exist_ok = True)

  def _chmod_dir(self, path: str, mode: int) -> None:
    dir = Path(path)
    dir.chmod(mode)
