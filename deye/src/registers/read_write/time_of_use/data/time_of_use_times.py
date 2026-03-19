from typing import List

from dataclasses import dataclass
from time_of_use_time import TimeOfUseTime

@dataclass
class TimeOfUseTimes:
  values: List[TimeOfUseTime]

  def check_bounds(self, items_count: int) -> None:
    if self.values and len(self.values) != items_count:
      raise ValueError(f'times count should be {items_count}')

  def check_time(self) -> None:
    if self.values[0].hour != 0 or self.values[0].minute != 0:
      raise ValueError(f'wrong item value {self.values[0]}: first item time should be 00:00')

    count = len(self.values)
    for i in range(count):
      time = self.values[i]
      next_time = self.values[(i + 1) % count]

      if not (0 <= time.hour <= 23):
        raise ValueError(f'wrong time value {time}: hour should be from 0 to 23')

      if not (0 <= time.minute <= 59):
        raise ValueError(f'wrong time value {time}: minute should be from 0 to 59')

      if time.minute % 5 != 0:
        raise ValueError(f'wrong time value {time}: minute should be a multiple of 5')

      if not TimeOfUseTimes.is_interval_correct(start = time, end = next_time):
        raise ValueError(f'wrong time interval {time}-{next_time}: end time should be greater than start')

  @staticmethod
  def is_interval_correct(
    start: TimeOfUseTime,
    end: TimeOfUseTime,
  ) -> bool:
    if start == end:
      return False

    # Check if next_time is 00:00 (end of the 24h cycle)
    is_midnight = end.hour == 0 and end.minute == 0
    return is_midnight or end >= start
