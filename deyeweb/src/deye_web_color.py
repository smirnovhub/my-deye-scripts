from enum import Enum

class DeyeWebColor(Enum):
  # Order matters, because id is increasing
  gray = '#dddddd'

  light_green = '#c1ffd1'
  green = '#20db50'

  light_yellow = '#fff0b3'
  yellow = '#ffcc00'

  light_red = '#ffb3b3'
  red = '#ff4d4d'

  _color: str
  _id: int

  @property
  def color(self) -> str:
    return self._color

  @property
  def id(self) -> int:
    return self._id

  def __new__(cls, color: str):
    obj = object.__new__(cls)
    obj._color = color
    obj._id = cls._next_value()
    obj._value_ = obj._id
    return obj

  @classmethod
  def _next_value(cls) -> int:
    # Collect all existing _value_ attributes of current enum members
    existing = [m._value_ for m in cls.__members__.values()]
    # Return the next integer value: one higher than the current maximum,
    # or 1 if there are no existing members yet
    return max(existing, default = -1) + 1
