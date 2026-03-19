from dataclasses import dataclass
from functools import total_ordering

@dataclass
@total_ordering
class TimeOfUseTime:
  """
  Represents a time value.

  Attributes:
      hour (int): Hour component (0-23).
      minute (int): Minute component (0-59).
  """
  hour: int
  minute: int

  def __eq__(self, other):
    if not isinstance(other, TimeOfUseTime):
      raise TypeError(f"Cannot compare TimeOfUseTime with {type(other).__name__}")
    return (self.hour, self.minute) == (other.hour, other.minute)

  def __lt__(self, other):
    if not isinstance(other, TimeOfUseTime):
      raise TypeError(f"Cannot compare TimeOfUseTime with {type(other).__name__}")
    return (self.hour, self.minute) < (other.hour, other.minute)

  def __str__(self) -> str:
    return f'{self.hour:02d}:{self.minute:02d}'
