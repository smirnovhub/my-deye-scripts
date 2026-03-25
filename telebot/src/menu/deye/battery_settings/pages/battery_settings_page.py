from enum import Enum

class BatterySettingsPage(Enum):
  # Needed to pass mypy checks
  _name: str
  _title: str

  main = ("Main", "Main")

  # Order matters here!
  shutdown_soc = ("Shutdown", "Battery shutdown SOC")
  low_batt_soc = ("Low Batt", "Battery low batt SOC")
  restart_soc = ("Restart", "Battery restart SOC")

  @property
  def name(self) -> str:
    return self._name

  @property
  def title(self) -> str:
    return self._title

  def __new__(cls, name: str, title: str):
    obj = object.__new__(cls)
    obj._name = name
    obj._title = title
    obj._value_ = cls._next_value()
    return obj

  @classmethod
  def _next_value(cls) -> int:
    # Collect all existing _value_ attributes of current enum members
    existing = [m._value_ for m in cls.__members__.values()]
    # Return the next integer value: one higher than the current maximum,
    # or 1 if there are no existing members yet
    return max(existing, default = -1) + 1
