import sys
import logging

from typing import List

from env_var import EnvVar
from env_vars import EnvVars

class DataCollectorConfig:
  def __init__(self):
    self.__data_collecting_interval_minutes = EnvVar("DATA_COLLECTING_INTERVAL_MINUTES", "180",
                                                     "Data collecting interval, sec")
    self.__data_retention_days = EnvVar("DATA_RETENTION_DAYS", "10", "Data retention time, days")
    self.__connection_lost_notify_after_minutes = EnvVar("CONN_LOST_NOTIFY_AFTER_MINUTES", "30",
                                                         "Notify about connection lost after, minutes")
    self.__connection_lost_notify_interval_minutes = EnvVar("CONN_LOST_NOTIFY_INTERVAL_MINUTES", "15",
                                                            "Notify about connection lost interval, minutes")

    self.__all_vars: List[EnvVar] = [
      EnvVars.DEYE_LOG_NAME,
      EnvVars.DEYE_DATA_COLLECTOR_DIR,
      self.__data_collecting_interval_minutes,
      self.__data_retention_days,
      self.__connection_lost_notify_after_minutes,
      self.__connection_lost_notify_interval_minutes,
    ]

  @property
  def LOG_NAME(self) -> str:
    return EnvVars.DEYE_LOG_NAME.value

  @property
  def DEYE_DATA_COLLECTOR_DIR(self) -> str:
    return EnvVars.DEYE_DATA_COLLECTOR_DIR.value

  @property
  def DATA_COLLECTING_INTERVAL_MINUTES(self) -> int:
    value = self.__data_collecting_interval_minutes.as_int()
    if not (60 <= value <= 900):
      raise ValueError(f"{self.__data_collecting_interval_minutes.name} should be from 60 to 900 sec")
    return value

  @property
  def DATA_RETENTION_DAYS(self) -> int:
    value = self.__data_retention_days.as_int()
    if not (1 <= value <= 365):
      raise ValueError(f"{self.__data_retention_days.name} should be from 1 to 365 days")
    return value

  @property
  def CONN_LOST_NOTIFY_AFTER_MINUTES(self) -> int:
    value = self.__connection_lost_notify_after_minutes.as_int()
    if not (10 <= value <= 720):
      raise ValueError(f"{self.__connection_lost_notify_after_minutes.name} should be from 10 to 720 minutes")
    return value

  @property
  def CONN_LOST_NOTIFY_INTERVAL_MINUTES(self) -> int:
    value = self.__connection_lost_notify_interval_minutes.as_int()
    if not (10 <= value <= 720):
      raise ValueError(f"{self.__connection_lost_notify_interval_minutes.name} should be from 10 to 720 minutes")
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
