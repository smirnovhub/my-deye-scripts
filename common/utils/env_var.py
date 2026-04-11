import os
import re

from env_utils import EnvUtils

class EnvVar:
  def __init__(self, name: str, default: str, description: str):
    self._name = name
    self._default = default
    self._description = description
    self._value = os.getenv(name, default).strip()

  @property
  def name(self) -> str:
    return self._name

  @property
  def default(self) -> str:
    return self._default

  @property
  def description(self) -> str:
    return self._description

  @property
  def value(self) -> str:
    return self._value

  def as_not_empty_value(self) -> str:
    if not self._value:
      raise RuntimeError(f"Environment variable '{self._name}' is not set")
    return self._value

  def as_not_empty_filtered_value(self) -> str:
    if not self._value:
      raise RuntimeError(f"Environment variable '{self._name}' is not set")

    val = self.as_filtered_value()
    if not val:
      raise RuntimeError(f"Environment variable '{self._name}' is empty")

    return val

  def as_filtered_value(self) -> str:
    return re.sub(r'[^a-zA-Z0-9-]+', '-', self._value).strip('-')

  def as_int(self) -> int:
    return int(self._value)

  def as_float(self) -> float:
    return float(self._value)

class LogNameEnvVar(EnvVar):
  def __init__(self):
    super().__init__(
      name = EnvUtils.DEYE_LOG_NAME,
      default = '',
      description = 'Individual folder name for logging',
    )
    # Will replace value from base class!
    self._value = EnvUtils.get_log_name()
