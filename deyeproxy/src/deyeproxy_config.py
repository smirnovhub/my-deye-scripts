import sys
import logging

from env_var import EnvVar

class DeyeProxyConfig:
  def __init__(self):
    self.__log_name = EnvVar("DEYE_LOG_NAME", "deyeproxy", "Individual folder name for logging")
    self.__logger_host = EnvVar("LOGGER_HOST", "", "IP/Hostname of the inverter logger (mandatory)")
    self.__logger_port = EnvVar("LOGGER_PORT", "8899", "Target port on the logger")
    self.__proxy_port = EnvVar("PROXY_PORT", "8899", "Local port to listen on")
    self.__max_connections = EnvVar("MAX_CONCURRENT_CONNECTIONS", "10", "Max simultaneous connections")
    self.__connect_timeout = EnvVar("CONNECT_TIMEOUT", "5", "Timeout for logger connection")
    self.__data_timeout = EnvVar("DATA_TIMEOUT", "10", "Inactivity timeout for session")
    self.__log_level = EnvVar("LOG_LEVEL", "INFO", "Log level for logging")

    self.__proxy_host = '0.0.0.0'

    self.__all_vars = [
      self.__log_name,
      self.__logger_host,
      self.__logger_port,
      self.__proxy_port,
      self.__max_connections,
      self.__connect_timeout,
      self.__data_timeout,
      self.__log_level,
    ]

    self.__logger = logging.getLogger()

  @property
  def LOG_NAME(self) -> str:
    return self.__log_name.as_filtered_value

  @property
  def LOGGER_HOST(self) -> str:
    return self.__logger_host.value

  @property
  def LOGGER_PORT(self) -> int:
    return self.__logger_port.as_int()

  @property
  def PROXY_HOST(self) -> str:
    return self.__proxy_host

  @property
  def PROXY_PORT(self) -> int:
    return self.__proxy_port.as_int()

  @property
  def MAX_CONCURRENT_CONNECTIONS(self) -> int:
    return self.__max_connections.as_int()

  @property
  def CONNECT_TIMEOUT(self) -> float:
    return self.__connect_timeout.as_float()

  @property
  def DATA_TIMEOUT(self) -> float:
    return self.__data_timeout.as_float()

  @property
  def LOG_LEVEL(self) -> str:
    return self.__log_level.value

  def _get_max_var_length(self) -> int:
    return max((len(var.name) for var in self.__all_vars), default = 0)

  def validate_or_exit(self):
    """Validate that mandatory settings are present, otherwise exit."""
    if not self.LOGGER_HOST:
      len = self._get_max_var_length()
      self.__logger.error(f"Environment variable '{self.__logger_host.name}' is not set. Exiting.")
      self.__logger.error("Available environment variables:")
      for var in self.__all_vars:
        default_str = f" (default: {var.default})" if var.default else ""
        self.__logger.error(f"  {var.name:<{len}} - {var.description}{default_str}")
      sys.exit(1)
