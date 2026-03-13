from typing import List

from dataclasses import dataclass
from time_of_use_charge import TimeOfUseCharge

@dataclass
class TimeOfUseCharges:
  values: List[TimeOfUseCharge]

  def validate(self, items_count: int) -> None:
    if self.values and len(self.values) != items_count:
      raise ValueError(f'charges count should be {items_count}')
