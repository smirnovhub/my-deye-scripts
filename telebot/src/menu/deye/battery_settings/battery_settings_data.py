from dataclasses import dataclass

@dataclass
class BatterySettingsData:
  shutdown_soc: int
  low_batt_soc: int
  restart_soc: int
