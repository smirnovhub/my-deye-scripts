import logging

from typing import List
from env_var import EnvVar
from env_vars import EnvVars

class DeyeStorageConfig:
  def __init__(self):
    self.__server_port = EnvVar("SERVER_PORT", "80", "Local port to listen on")
    self.__max_keys_count = EnvVar("MAX_KEYS_COUNT", "32", "Maximum number of top-level keys in storage")
    self.__max_json_size = EnvVar("MAX_JSON_SIZE", str(32 * 1024), "Maximum JSON size in bytes for incoming POST body")
    self.__max_json_storage_size = EnvVar("MAX_JSON_STORAGE_SIZE", str(256 * 1024),
                                          "Maximum total JSON storage size per key in bytes")

    self.__server_host = '0.0.0.0'

    self.__all_vars: List[EnvVar] = [
      EnvVars.DEYE_LOG_NAME,
      self.__server_port,
      self.__max_keys_count,
      self.__max_json_size,
      self.__max_json_storage_size,
    ]

  @property
  def LOG_NAME(self) -> str:
    return EnvVars.DEYE_LOG_NAME.value

  @property
  def SERVER_HOST(self) -> str:
    return self.__server_host

  @property
  def SERVER_PORT(self) -> int:
    return self.__server_port.as_int()

  @property
  def MAX_KEYS_COUNT(self) -> int:
    return self.__max_keys_count.as_int()

  @property
  def MAX_JSON_SIZE(self) -> int:
    return self.__max_json_size.as_int()

  @property
  def MAX_JSON_STORAGE_SIZE(self) -> int:
    return self.__max_json_storage_size.as_int()

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
