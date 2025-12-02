from typing import List

from dataclasses import dataclass

from time_of_use_item import TimeOfUseItem
from time_of_use_week import TimeOfUseWeek

@dataclass
class TimeOfUseData:
  """
  Represents a time-of-use schedule, including its activation state,
  the list of time-of-use items, and the weekly applicability.

  Attributes:
      enabled (bool): Indicates whether the time-of-use schedule is active.
      items (List[TimeOfUseItem]): A list of time-of-use entries, each containing
          time information along with power and state-of-charge values.
      weekly (TimeOfUseWeek): The days of the week on which this time-of-use schedule applies.
  """
  enabled: bool
  items: List[TimeOfUseItem]
  weekly: TimeOfUseWeek

  def validate(self, min_soc: int, max_power: int):
    """
    Validates the TimeOfUseData items according to several rules.

    Checks performed:
    1. The list must contain exactly 6 items.
    2. The first item's time must be 00:00.
    3. Each item's power must be between 0 and `max_power`.
    4. Each item's state of charge (SOC) must be between `min_soc` and 100.
    5. Each item's hour must be between 0 and 23.
    6. Each item's minute must be between 0 and 59.
    7. Each item's minute must be a multiple of 5.
    8. Each subsequent item's time must be strictly greater than the previous item's time.

    Args:
        min_soc (int): Minimum allowed state of charge.
        max_power (int): Maximum allowed power.

    Raises:
        ValueError: If any of the validation rules are violated.
    """
    items_count = 6

    if len(self.items) != items_count:
      raise ValueError(f'items count should be {items_count}')

    if self.items[0].time.hour != 0 or self.items[0].time.minute != 0:
      raise ValueError(f'wrong item {self.items[0].time}: first item time should be 00:00')

    for item in self.items:
      if not (0 <= item.power <= max_power):
        raise ValueError(f'wrong item {item.time}: power should be from 0 to {max_power}')

      if not (min_soc <= item.soc <= 100):
        raise ValueError(f'wrong item {item.time}: soc should be from {min_soc} to 100')

      if not (0 <= item.time.hour <= 23):
        raise ValueError(f'wrong item {item.time}: hour should be from 0 to 23')

      if not (0 <= item.time.minute <= 59):
        raise ValueError(f'wrong item {item.time}: minute should be from 0 to 59')

      if item.time.minute % 5 != 0:
        raise ValueError(f'wrong item {item.time}: minute should be a multiple of 5')

    for i in range(1, len(self.items)):
      prev = self.items[i - 1]
      curr = self.items[i]

      prev_minutes = prev.time.hour * 60 + prev.time.minute
      curr_minutes = curr.time.hour * 60 + curr.time.minute

      if curr_minutes < prev_minutes:
        raise ValueError(f'wrong item {self.items[i].time}: each next time should be greater or equal to previous')

  def __str__(self) -> str:
    items = "; ".join(str(item) for item in self.items)
    return f'enabled={self.enabled}; {items}; {self.weekly}'.lower()
