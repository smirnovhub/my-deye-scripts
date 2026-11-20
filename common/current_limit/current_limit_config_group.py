from enum import Enum, auto

class CurrentLimitConfigGroup(Enum):
  info = auto()
  dont_regulate = auto()
  charging = auto()
  winter = auto()
