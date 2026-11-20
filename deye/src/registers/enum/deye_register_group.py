from enum import Enum

class DeyeRegisterGroup(Enum):
  pv = "PV"
  load = "Load"
  grid = "Grid"
  gen = "Gen"
  battery = "Battery"
  inverter = "Inverter"
  test = "Test"

  _title: str

  @property
  def title(self) -> str:
    return self._title

  def __new__(cls, title: str):
    obj = object.__new__(cls)
    obj._title = title
    obj._value_ = title
    return obj
