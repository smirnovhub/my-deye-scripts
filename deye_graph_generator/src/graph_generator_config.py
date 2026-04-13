import sys
import logging

from typing import List
from env_var import EnvVar, LogNameEnvVar
from env_utils import EnvUtils

class GraphGeneratorConfig:
  def __init__(self):
    self.__log_name = LogNameEnvVar()
    self.__remote_graph_server_url = EnvVar(EnvUtils.REMOTE_GRAPH_SERVER_URL, "", "Remote graph server URL")
    self.__deye_graphs_dir = EnvVar(EnvUtils.DEYE_GRAPHS_DIR, "", "Directory for PNG files")
    self.__graphs_generate_period_minutes = EnvVar("PERIOD", "10", "Graphs generate period, minutes")
    self.__graphs_generate_delay_sec = EnvVar("DELAY", "30", "Graphs generate delay, sec")

    self.__all_vars: List[EnvVar] = [
      self.__log_name,
      self.__remote_graph_server_url,
      self.__deye_graphs_dir,
      self.__graphs_generate_period_minutes,
      self.__graphs_generate_delay_sec,
    ]

  @property
  def LOG_NAME(self) -> str:
    return self.__log_name.as_not_empty_value()

  @property
  def REMOTE_GRAPH_SERVER_URL(self) -> str:
    return self.__remote_graph_server_url.as_not_empty_value()

  @property
  def DEYE_GRAPHS_DIR(self) -> str:
    return self.__deye_graphs_dir.as_not_empty_filtered_value()

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
