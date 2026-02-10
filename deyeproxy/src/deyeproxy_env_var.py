import os

class DeyeProxyEnvVar:
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

  def as_int(self) -> int:
    return int(self.__value)

  def as_float(self) -> float:
    return float(self.__value)
