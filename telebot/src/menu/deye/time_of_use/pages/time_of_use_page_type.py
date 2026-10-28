from enum import Enum, auto

class TimeOfUsePageType(Enum):
  enable = auto()
  main = auto()
  edit = auto()
  start_hours = auto()
  start_minutes = auto()
  end_hours = auto()
  end_minutes = auto()
  powers = auto()
  socs = auto()
  undo = auto()
