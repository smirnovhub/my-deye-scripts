import os
import re

from env_utils import EnvUtils

class EnvVar:
  def __init__(self, name: str, default: str, description: str):
    self.__name = name
    self.__default = default
    self.__description = description
    self.__value = os.getenv(name, default)

  @property
  def name(self) -> str:
    return self.__name

  @property
  def default(self) -> str:
    return self.__default

  @property
  def description(self) -> str:
    return self.__description

  @property
  def value(self) -> str:
    return self.__value

  def as_filtered_value(self) -> str:
    return re.sub(r'[^a-zA-Z0-9-]+', '-', self.__value).strip('-')

  def as_int(self) -> int:
    return int(self.__value)

  def as_float(self) -> float:
    return float(self.__value)

class LogNameEnvVar(EnvVar):
  def __init__(self):
    super().__init__(
      name = "DEYE_LOG_NAME",
      default = '',
      description = 'Individual folder name for logging',
    )
    # Will replace value from base class!
    self.__value = EnvUtils.get_log_name()
