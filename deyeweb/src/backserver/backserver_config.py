import logging

from typing import List
from env_var import EnvVar, LogNameEnvVar

class BackServerConfig:
  def __init__(self):
    self.__log_name = LogNameEnvVar()
    self.__server_port = EnvVar("SERVER_PORT", "80", "Local port to listen on")
    self.__back_execution_timeout = EnvVar("BACK_EXECUTION_TIMEOUT", "15", "Timeout for back requests execution, s")
    self.__server_host = '0.0.0.0'

    self.__all_vars: List[EnvVar] = [
      self.__log_name,
      self.__server_port,
      self.__back_execution_timeout,
    ]

  @property
  def LOG_NAME(self) -> str:
    return self.__log_name.value

  @property
  def SERVER_HOST(self) -> str:
    return self.__server_host

  @property
  def SERVER_PORT(self) -> int:
    return self.__server_port.as_int()

  @property
  def BACK_EXECUTION_TIMEOUT(self) -> float:
    return self.__back_execution_timeout.as_float()

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
      logger.info(f"{var.name:<{len}} : {var.value}")
