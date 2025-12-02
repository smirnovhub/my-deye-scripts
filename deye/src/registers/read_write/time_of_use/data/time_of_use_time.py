from dataclasses import dataclass

@dataclass
class TimeOfUseTime:
  """
  Represents a time value.

  Attributes:
      hour (int): Hour component (0-23).
      minute (int): Minute component (0-59).
  """
  hour: int
  minute: int

  def __str__(self) -> str:
    return f'{self.hour:02d}:{self.minute:02d}'
