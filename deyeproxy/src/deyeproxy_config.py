import sys

from src.deyeproxy_env_var import DeyeProxyEnvVar

class DeyeProxyConfig:
  def __init__(self):
    self._logger_host_var = DeyeProxyEnvVar("LOGGER_HOST", "", "IP/Hostname of the inverter logger (mandatory)")
    logger_port_var = DeyeProxyEnvVar("LOGGER_PORT", "8899", "Target port on the logger")
    proxy_port_var = DeyeProxyEnvVar("PROXY_PORT", "8899", "Local port to listen on")
    max_connections_var = DeyeProxyEnvVar("MAX_CONCURRENT_CONNECTIONS", "10", "Max simultaneous connections")
    connect_timeout_var = DeyeProxyEnvVar("CONNECT_TIMEOUT", "5", "Timeout for logger connection")
    data_timeout_var = DeyeProxyEnvVar("DATA_TIMEOUT", "10", "Inactivity timeout for session")
    log_level_var = DeyeProxyEnvVar("LOG_LEVEL", "INFO", "Log level for logging")

    self.LOGGER_HOST = self._logger_host_var.value
    self.LOGGER_PORT = logger_port_var.as_int()
    self.PROXY_HOST = '0.0.0.0'
    self.PROXY_PORT = proxy_port_var.as_int()
    self.MAX_CONCURRENT_CONNECTIONS = max_connections_var.as_int()
    self.CONNECT_TIMEOUT = connect_timeout_var.as_float()
    self.DATA_TIMEOUT = data_timeout_var.as_float()
    self.LOG_LEVEL = log_level_var.value

    self._all_vars = [
      self._logger_host_var,
      logger_port_var,
      proxy_port_var,
      max_connections_var,
      connect_timeout_var,
      data_timeout_var,
      log_level_var,
    ]

  def validate_or_exit(self):
    if not self.LOGGER_HOST:
      print(f"Environment variable '{self._logger_host_var.name}' is not set. Exiting.")
      print("\nAvailable environment variables:")
      for var in self._all_vars:
        default_str = f" (default: {var.default})" if var.default else ""
        print(f"  {var.name:<26} - {var.description}{default_str}")
      sys.exit(1)
