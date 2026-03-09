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

    # Maximum time (in seconds) allowed to establish the TCP connection to the logger.
    # If the connection attempt does not complete within this time, a socket.timeout
    # exception is raised and the session is aborted.
    self.__connect_timeout = EnvVar("CONNECT_TIMEOUT", "5", "Timeout for logger connection")

    # Maximum inactivity time (in seconds) while waiting for data from the client.
    # If the client does not send any data within this period, the proxy assumes
    # the client connection is idle or stalled and terminates the session.
    self.__client_idle_timeout = EnvVar("CLIENT_IDLE_TIMEOUT", "3", "Inactivity timeout for client")

    # Maximum inactivity time (in seconds) while waiting for data from the logger device.
    # If no data is received from the logger within this period, the proxy assumes
    # the logger connection is stalled or broken and terminates the session.
    self.__logger_idle_timeout = EnvVar("LOGGER_IDLE_TIMEOUT", "5", "Inactivity timeout for logger")

    # Maximum total lifetime of a session (in seconds), regardless of activity.
    # When this limit is reached, the proxy forcibly terminates the session to
    # ensure the logger resource is eventually released.
    self.__session_timeout = EnvVar("SESSION_TIMEOUT", "10", "Maximum duration for session")

    self.__log_level = EnvVar("LOG_LEVEL", "INFO", "Log level for logging")

    self.__proxy_host = '0.0.0.0'

    self.__all_vars = [
      self.__log_name,
      self.__logger_host,
      self.__logger_port,
      self.__proxy_port,
      self.__max_connections,
      self.__connect_timeout,
      self.__client_idle_timeout,
      self.__logger_idle_timeout,
      self.__session_timeout,
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
  def CLIENT_IDLE_TIMEOUT(self) -> float:
    return self.__client_idle_timeout.as_float()

  @property
  def LOGGER_IDLE_TIMEOUT(self) -> float:
    return self.__logger_idle_timeout.as_float()

  @property
  def SESSION_TIMEOUT(self) -> float:
    return self.__session_timeout.as_float()

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
