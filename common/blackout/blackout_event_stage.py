from dataclasses import dataclass
from datetime import datetime

from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.types import SerializationStrategy

from blackout_stage import BlackoutStage

class MyDateTimeStrategy(SerializationStrategy):
  # Serializing datetime to your specific string format
  def serialize(self, value: datetime) -> str:
    return value.strftime('%Y-%m-%d %H:%M:%S')

  # Deserializing string back to datetime object
  def deserialize(self, value: str) -> datetime:
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

class SchedulerStageStrategy(SerializationStrategy):
  # Serializing enum member to its name (string)
  def serialize(self, value: BlackoutStage) -> str:
    return value.name

  # Deserializing string name back to enum member
  def deserialize(self, value: str) -> BlackoutStage:
    return BlackoutStage[value]

@dataclass
class BlackoutEventStage(DataClassJSONMixin):
  # Next stage name of event processing
  # Actual for current active event only
  stage: BlackoutStage
  # Event data/time in format 2026-03-16 23:15:47
  run_date: datetime

  class Config(BaseConfig):
    # Apply strategies to specific types in this class
    serialization_strategy = {
      datetime: MyDateTimeStrategy(),
      BlackoutStage: SchedulerStageStrategy(),
    }
