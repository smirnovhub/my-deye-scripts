from enum import Enum, auto

class BlackoutAction(Enum):
  test = auto()
  empty = auto()
  stop_charging = auto()
  switch_to_battery = auto()
  turn_grid_off = auto()
