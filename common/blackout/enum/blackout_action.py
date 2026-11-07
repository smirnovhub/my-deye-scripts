from enum import Enum

class BlackoutAction(Enum):
  test = 'Test'
  empty = 'Empty'
  stop_charging = 'Stop Charging'
  switch_to_battery = 'Switch To Battery'
  turn_grid_off = 'Turn Grid Off'

  _title: str

  @property
  def title(self) -> str:
    return self._title

  def __new__(cls, title: str):
    obj = object.__new__(cls)
    obj._title = title
    obj._value_ = title
    return obj
