from dataclasses import dataclass

from time_of_use_charge import TimeOfUseCharge
from time_of_use_time import TimeOfUseTime

@dataclass
class TimeOfUseItem:
  """
  Represents a single time-of-use entry.

  Attributes:
      charge (TimeOfUseCharge): Object containing grid and gen charge flags.
      time (TimeOfUseTime): Time object containing hour and minute values.
      power (int): Power value for the interval.
      soc (int): State of charge value.
  """
  charge: TimeOfUseCharge
  time: TimeOfUseTime
  power: int
  soc: int

  def __str__(self) -> str:
    return f'charge={self.charge}, time={self.time}, power={self.power}, soc={self.soc}'
