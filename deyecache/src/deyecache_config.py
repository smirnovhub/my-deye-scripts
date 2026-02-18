import logging

from src.deyecache_env_var import DeyeCacheEnvVar

class DeyeCacheConfig:
  def __init__(self):
    self.__server_port = DeyeCacheEnvVar("SERVER_PORT", "80", "Local port to listen on")
    self.__max_keys_count = DeyeCacheEnvVar("MAX_KEYS_COUNT", "32", "Maximum number of top-level keys in cache storage")
    self.__max_json_size = DeyeCacheEnvVar("MAX_JSON_SIZE", str(32 * 1024),
                                           "Maximum JSON size in bytes for incoming POST body")
    self.__max_json_storage_size = DeyeCacheEnvVar("MAX_JSON_STORAGE_SIZE", str(256 * 1024),
                                                   "Maximum total JSON storage size per key in bytes")

    self.__server_host = '0.0.0.0'

    self.__all_vars = [
      self.__server_port,
      self.__max_keys_count,
      self.__max_json_size,
      self.__max_json_storage_size,
    ]

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

  def print_usage(self):
    print("\nAvailable environment variables:")
    for var in self.__all_vars:
      default_str = f" (default: {var.default})" if var.default else ""
      print(f"  {var.name:<21} - {var.description}{default_str}")
    print("")

  def print_config(self, logger: logging.Logger):
    for var in self.__all_vars:
      logger.info(f"{var.name:<21} : {var.value}")
