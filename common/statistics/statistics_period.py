from enum import Enum
from datetime import date

class StatisticsPeriod(Enum):
  _description: str
  _date_format: str

  day = ("Day", "%Y-%m-%d")
  month = ("Month", "%Y-%m")
  year = ("Year", "%Y")

  @property
  def description(self) -> str:
    return self._description

  @property
  def date_format(self) -> str:
    return self._date_format

  def get_date_suffix(self, today: date) -> str:
    return today.strftime(self._date_format)

  def __new__(cls, description: str, date_format: str):
    obj = object.__new__(cls)
    obj._value_ = cls._next_value()
    obj._date_format = date_format
    obj._description = description
    return obj

  @classmethod
  def _next_value(cls):
    # Collect all existing _value_ attributes of current enum members
    existing = [m._value_ for m in cls.__members__.values()]
    # Return the next integer value: one higher than the current maximum,
    # or 1 if there are no existing members yet
    return max(existing, default = 0) + 1
