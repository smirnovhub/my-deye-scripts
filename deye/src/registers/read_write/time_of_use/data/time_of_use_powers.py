from typing import List

from dataclasses import dataclass

@dataclass
class TimeOfUsePowers:
  values: List[int]

  def validate(self, items_count: int, max_power: int) -> None:
    if self.values and len(self.values) != items_count:
      raise ValueError(f'powers count should be {items_count}')

    for value in self.values:
      if not (0 <= value <= max_power):
        raise ValueError(f'wrong power value {value}: power should be from 0 to {max_power}')
