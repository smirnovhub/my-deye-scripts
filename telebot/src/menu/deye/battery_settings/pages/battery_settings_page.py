from enum import Enum, auto

class BatterySettingsPage(Enum):
  main = auto()
  # Order matters here!
  shutdown_soc = auto()
  low_batt_soc = auto()
  restart_soc = auto()
