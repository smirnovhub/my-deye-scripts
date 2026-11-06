from enum import Enum

class CellAlign(Enum):
  _align_value: str

  center = "center"
  left = "left"
  right = "right"

  @property
  def value(self) -> str:
    return self._align_value

  def __new__(cls, value: str):
    obj = object.__new__(cls)
    obj._align_value = value
    obj._value_ = value
    return obj
