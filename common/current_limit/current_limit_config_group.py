from enum import Enum

class CurrentLimitConfigGroup(Enum):
  _group_value: str

  charging = "Charging"
  winter = "Winter"

  @property
  def value(self) -> str:
    return self._group_value

  def __new__(cls, value: str):
    obj = object.__new__(cls)
    obj._group_value = value
    obj._value_ = value
    return obj
