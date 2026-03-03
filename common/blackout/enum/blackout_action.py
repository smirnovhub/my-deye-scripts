from enum import Enum

class BlackoutAction(Enum):
  test = 'Test'
  empty = 'Empty'
  stop_charging = 'Stop Charging'
  switch_to_battery = 'Switch To Battery'
  turn_grid_off = 'Turn Grid Off'

  # Needed to pass mypy checks
  _title: str

  @property
  def title(self) -> str:
    return self._title

  def __new__(cls, title: str):
    obj = object.__new__(cls)
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
