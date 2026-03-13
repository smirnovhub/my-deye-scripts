from typing import List

from dataclasses import dataclass
from time_of_use_time import TimeOfUseTime

@dataclass
class TimeOfUseTimes:
  values: List[TimeOfUseTime]

  def validate(self, items_count: int) -> None:
    if self.values and len(self.values) != items_count:
      raise ValueError(f'times count should be {items_count}')

    for value in self.values:
      if not (0 <= value.hour <= 23):
        raise ValueError(f'wrong time value {value}: hour should be from 0 to 23')

      if not (0 <= value.minute <= 59):
        raise ValueError(f'wrong time value {value}: minute should be from 0 to 59')

      if value.minute % 5 != 0:
        raise ValueError(f'wrong time value {value}: minute should be a multiple of 5')
