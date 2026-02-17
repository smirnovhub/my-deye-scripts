from src.deyecache_env_var import DeyeCacheEnvVar

class DeyeCacheConfig:
  def __init__(self):
    self.__server_port = DeyeCacheEnvVar("SERVER_PORT", "5000", "Local port to listen on")

    self.__server_host = '0.0.0.0'

    self.__all_vars = [
      self.__server_port,
    ]

  @property
  def SERVER_HOST(self) -> str:
    return self.__server_host

  @property
  def SERVER_PORT(self) -> int:
    return self.__server_port.as_int()

  def print_usage(self):
    print("\nAvailable environment variables:")
    for var in self.__all_vars:
      default_str = f" (default: {var.default})" if var.default else ""
      print(f"  {var.name:<11} - {var.description}{default_str}")
    print("")
