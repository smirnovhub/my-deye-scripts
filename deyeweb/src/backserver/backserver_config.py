import logging

from backserver_env_var import BackServerEnvVar

class BackServerConfig:
  def __init__(self):
    self.__server_port = BackServerEnvVar("SERVER_PORT", "80", "Local port to listen on")
    self.__back_execution_timeout = BackServerEnvVar("BACK_EXECUTION_TIMEOUT", "15",
                                                     "Timeout for back requests execution, s")
    self.__server_host = '0.0.0.0'

    self.__all_vars = [
      self.__server_port,
      self.__back_execution_timeout,
    ]

  @property
  def SERVER_HOST(self) -> str:
    return self.__server_host

  @property
  def SERVER_PORT(self) -> int:
    return self.__server_port.as_int()

  @property
  def BACK_EXECUTION_TIMEOUT(self) -> float:
    return self.__back_execution_timeout.as_float()

  def print_usage(self):
    print("\nAvailable environment variables:")
    for var in self.__all_vars:
      default_str = f" (default: {var.default})" if var.default else ""
      print(f"  {var.name:<22} - {var.description}{default_str}")
    print("")

  def print_config(self, logger: logging.Logger):
    for var in self.__all_vars:
      logger.info(f"{var.name:<22} : {var.value}")
