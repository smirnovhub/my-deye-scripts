import os

class DeyeProxyEnvVar:
  def __init__(self, name: str, default: str, description: str):
    self.name = name
    self.default = default
    self.description = description
    self.value = os.getenv(name, default)

  def as_int(self) -> int:
    return int(self.value)

  def as_float(self) -> float:
    return float(self.value)
