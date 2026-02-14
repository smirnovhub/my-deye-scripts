from enum import Enum

class DeyeWebSection(Enum):
  info = 'Info'
  today = 'Today'
  total = 'Total'
  settings = 'Settings'
  forecast = 'Forecast'
  time_of_use_soc = 'Time Of Use SOC'
  grid_connect_voltage_low = 'Grid LowV'
  time_of_use_power = 'Time Of Use Power'
  battery_max_charge_current = 'Max Charge Current'
  battery_grid_charge_current = 'Grid Charge Current'
  battery_gen_charge_current = 'Gen Charge Current'
  grid_reconnection_time = 'Grid Reconnection'
  grid_peak_shaving_power = 'Grid Peak Shaving'
  bms = 'BMS'
  service = 'Service'

  @property
  def title(self) -> str:
    return self._title

  @property
  def id(self) -> str:
    return self._id

  def __new__(cls, title: str):
    obj = object.__new__(cls)
    obj._title = title
    obj._id = title.replace(' ', '_').lower()
    obj._value_ = cls._next_value()
    return obj

  @classmethod
  def _next_value(cls) -> int:
    # Collect all existing _value_ attributes of current enum members
    existing = [m._value_ for m in cls.__members__.values()]
    # Return the next integer value: one higher than the current maximum,
    # or 1 if there are no existing members yet
    return max(existing, default = -1) + 1
