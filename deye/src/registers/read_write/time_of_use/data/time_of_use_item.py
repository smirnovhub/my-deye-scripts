from dataclasses import dataclass

from time_of_use_time import TimeOfUseTime

@dataclass
class TimeOfUseItem:
  """
  Represents a single time-of-use entry.

  Attributes:
      time (TimeOfUseTime): Time object containing hour and minute values.
      power (int): Power value for the interval.
      soc (int): State of charge value.
  """
  time: TimeOfUseTime
  power: int
  soc: int
  grid_charge: bool
  gen_charge: bool

  def __str__(self) -> str:
    return f'grid_charge={self.grid_charge}, gen_charge={self.gen_charge}, time={self.time}, power={self.power}, soc={self.soc}'
