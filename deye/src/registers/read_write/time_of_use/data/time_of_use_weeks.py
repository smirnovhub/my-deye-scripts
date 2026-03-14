from typing import List

from dataclasses import dataclass

from time_of_use_week import TimeOfUseWeek

@dataclass
class TimeOfUseWeeks:
  values: List[TimeOfUseWeek]

  def validate(self, items_count: int) -> None:
    if self.values and len(self.values) != items_count:
      raise ValueError(f'weeks count should be {items_count}')
