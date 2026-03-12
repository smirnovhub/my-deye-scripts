from enum import Enum, auto

class TimeOfUseButtonType(Enum):
  back = auto()
  reset = auto()
  switch = auto()
  start_time = auto()
  start_hour = auto()
  start_minute = auto()
  end_time = auto()
  end_hour = auto()
  end_minute = auto()
  power = auto()
  power_watt = auto()
  soc = auto()
  soc_percent = auto()
