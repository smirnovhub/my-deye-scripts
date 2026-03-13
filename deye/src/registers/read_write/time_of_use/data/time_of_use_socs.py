from typing import List

from dataclasses import dataclass

@dataclass
class TimeOfUseSocs:
  values: List[int]

  def validate(self, items_count: int, min_soc: int) -> None:
    if self.values and len(self.values) != items_count:
      raise ValueError(f'socs count should be {items_count}')

    for value in self.values:
      if not (min_soc <= value <= 100):
        raise ValueError(f'wrong soc value {value}: soc should be from {min_soc} to 100')
