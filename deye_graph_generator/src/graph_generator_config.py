import sys
import logging

from typing import List
from env_var import EnvVar
from env_vars import EnvVars

class GraphGeneratorConfig:
  def __init__(self):
    self.__graphs_generate_period_minutes = EnvVar("PERIOD", "10", "Graphs generate period, minutes")
    self.__graphs_generate_delay_sec = EnvVar("DELAY", "30", "Graphs generate delay, sec")

    self.__all_vars: List[EnvVar] = [
      EnvVars.DEYE_LOG_NAME,
      EnvVars.REMOTE_GRAPH_SERVER_URL,
      EnvVars.DEYE_GRAPHS_DIR,
      EnvVars.DEYE_GRAPHS_FORMAT,
      self.__graphs_generate_period_minutes,
      self.__graphs_generate_delay_sec,
    ]

  @property
  def LOG_NAME(self) -> str:
    return EnvVars.DEYE_LOG_NAME.value

  @property
  def REMOTE_GRAPH_SERVER_URL(self) -> str:
    return EnvVars.REMOTE_GRAPH_SERVER_URL.value

  @property
  def DEYE_GRAPHS_DIR(self) -> str:
    return EnvVars.DEYE_GRAPHS_DIR.value

  @property
  def DEYE_GRAPHS_FORMAT(self) -> str:
    return EnvVars.DEYE_GRAPHS_FORMAT.value

  @property
  def PERIOD(self) -> int:
    return self.__graphs_generate_period_minutes.as_int()

  @property
  def DELAY(self) -> int:
    return self.__graphs_generate_delay_sec.as_int()

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
