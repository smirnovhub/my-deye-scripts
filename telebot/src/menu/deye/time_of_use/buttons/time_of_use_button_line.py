from dataclasses import dataclass

from time_of_use_item import TimeOfUseItem
from time_of_use_buttons import TimeOfUseButtons

@dataclass
class TimeOfUseButtonLine:
  index: int
  item: TimeOfUseItem
  buttons: TimeOfUseButtons
