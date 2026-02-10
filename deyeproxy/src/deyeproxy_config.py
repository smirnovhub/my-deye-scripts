import sys

from src.deyeproxy_env_var import DeyeProxyEnvVar

class DeyeProxyConfig:
  def __init__(self):
    self.__logger_host = DeyeProxyEnvVar("LOGGER_HOST", "", "IP/Hostname of the inverter logger (mandatory)")
    self.__logger_port = DeyeProxyEnvVar("LOGGER_PORT", "8899", "Target port on the logger")
    self.__proxy_port = DeyeProxyEnvVar("PROXY_PORT", "8899", "Local port to listen on")
    self.__max_connections = DeyeProxyEnvVar("MAX_CONCURRENT_CONNECTIONS", "10", "Max simultaneous connections")
    self.__connect_timeout = DeyeProxyEnvVar("CONNECT_TIMEOUT", "5", "Timeout for logger connection")
    self.__data_timeout = DeyeProxyEnvVar("DATA_TIMEOUT", "10", "Inactivity timeout for session")
    self.__log_level = DeyeProxyEnvVar("LOG_LEVEL", "INFO", "Log level for logging")

    self.__proxy_host = '0.0.0.0'

    self.__all_vars = [
      self.__logger_host,
      self.__logger_port,
      self.__proxy_port,
      self.__max_connections,
      self.__connect_timeout,
      self.__data_timeout,
      self.__log_level,
    ]

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

  def validate_or_exit(self):
    """Validate that mandatory settings are present, otherwise exit."""
    if not self.LOGGER_HOST:
      print(f"Environment variable '{self.__logger_host.name}' is not set. Exiting.")
      print("\nAvailable environment variables:")
      for var in self.__all_vars:
        default_str = f" (default: {var.default})" if var.default else ""
        print(f"  {var.name:<26} - {var.description}{default_str}")
      sys.exit(1)
