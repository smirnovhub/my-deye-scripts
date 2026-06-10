from typing import List
from datetime import date

from dataclasses import dataclass, field

from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.types import SerializationStrategy

class MyDateStrategy(SerializationStrategy):
  # Serializing date to your specific string format
  def serialize(self, value: date) -> str:
    return value.isoformat()

  # Deserializing string back to date object
  def deserialize(self, value: str) -> date:
    return date.fromisoformat(value)

@dataclass
class CurrentLimitConfigDto(DataClassJSONMixin):
  battery_charge_lost_coef: float = 1.8
  last_max_charge_current: int = 0
  last_full_charge_date: date = date.min
  dont_regulate_dates: List[date] = field(default_factory = list)

  class Config(BaseConfig):
    # Apply strategies to specific types in this class
    serialization_strategy = {
      date: MyDateStrategy(),
    }
