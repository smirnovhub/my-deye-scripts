import sys
import logging

from typing import List
from env_var import EnvVar, LogNameEnvVar

class DataCollectorConfig:
  def __init__(self):
    self.__log_name = LogNameEnvVar()
    self.__data_collecting_interval = EnvVar("DATA_COLLECTING_INTERVAL", "180", "Data collecting interval, sec")
    self.__data_retention_days = EnvVar("DATA_RETENTION_DAYS", "7", "Data retention time, days")

    self.__all_vars: List[EnvVar] = [
      self.__log_name,
      self.__data_collecting_interval,
      self.__data_retention_days,
    ]

  @property
  def LOG_NAME(self) -> str:
    return self.__log_name.value

  @property
  def DATA_COLLECTING_INTERVAL(self) -> int:
    value = self.__data_collecting_interval.as_int()
    if not (60 <= value <= 900):
      raise ValueError(f"{self.__data_collecting_interval.name} should be from 60 to 900 sec")
    return value

  @property
  def DATA_RETENTION_DAYS(self) -> int:
    value = self.__data_retention_days.as_int()
    if not (1 <= value <= 30):
      raise ValueError(f"{self.__data_collecting_interval.name} should be from 1 to 30 days")
    return value

  def _get_max_var_length(self) -> int:
    return max((len(var.name) for var in self.__all_vars), default = 0)

  def print_usage(self, logger: logging.Logger):
    logger.info("Available environment variables:")
    len = self._get_max_var_length()
    for var in self.__all_vars:
      default_str = f" (default: {var.default})" if var.default else ""
      logger.info(f"  {var.name:<{len}} - {var.description}{default_str}")

  def print_config(self, logger: logging.Logger):
    len = self._get_max_var_length()
    for var in self.__all_vars:
      val = "********" if "pass" in var.name.lower() else var.value
      logger.info(f"{var.name:<{len}} : {val}")

  def validate_or_exit(self, logger: logging.Logger):
    for var in self.__all_vars:
      if not var.value:
        self.print_usage(logger)
        logger.info(f"  {var.name} can't be empty")
        sys.exit(1)
