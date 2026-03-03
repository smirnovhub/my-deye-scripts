from datetime import datetime
from dataclasses import dataclass

from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.types import SerializationStrategy

from blackout_action import BlackoutAction
from blackout_event_stage import BlackoutEventStage

class MyDateTimeStrategy(SerializationStrategy):
  # Serializing datetime to your specific string format
  def serialize(self, value: datetime) -> str:
    return value.strftime('%Y-%m-%d %H:%M:%S')

  # Deserializing string back to datetime object
  def deserialize(self, value: str) -> datetime:
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

class SchedulerActionStrategy(SerializationStrategy):
  # Serializing enum member to its name (string)
  def serialize(self, value: BlackoutAction) -> str:
    return value.name

  # Deserializing string name back to enum member
  def deserialize(self, value: str) -> BlackoutAction:
    return BlackoutAction[value]

@dataclass
class BlackoutCurrentEvent(DataClassJSONMixin):
  # Event data/time in format 2026-03-16 23:15:47
  date: datetime
  # Any arbitrary event name for visual representation
  name: str
  # Action name of event (turn off grid, stop charging, move to battery, etc.)
  action: BlackoutAction
  # Next stage name of event processing
  # Actual for current active event only
  stage: BlackoutEventStage
  # True if event force finish requested
  # Actual for current active event only
  force_finish: bool = False
  # True if event force stop requested
  # Actual for current active event only
  force_stop: bool = False

  class Config(BaseConfig):
    # Apply strategies to specific types in this class
    serialization_strategy = {
      datetime: MyDateTimeStrategy(),
      BlackoutAction: SchedulerActionStrategy(),
    }
