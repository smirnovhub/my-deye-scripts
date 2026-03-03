from datetime import datetime
from dataclasses import dataclass

from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.types import SerializationStrategy

from blackout_action import BlackoutAction
from blackout_stage import BlackoutStage

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
    try:
      return BlackoutAction[value]
    except (KeyError, TypeError):
      return BlackoutAction.empty

class SchedulerStageStrategy(SerializationStrategy):
  # Serializing enum member to its name (string)
  def serialize(self, value: BlackoutStage) -> str:
    return value.name

  # Deserializing string name back to enum member
  def deserialize(self, value: str) -> BlackoutStage:
    try:
      return BlackoutStage[value]
    except (KeyError, TypeError):
      return BlackoutStage.stage1

@dataclass
class BlackoutEvent(DataClassJSONMixin):
  # Event data/time in format 2026-03-16 23:15:47
  date: datetime
  # Any arbitrary event name for visual representation
  name: str = ""
  # Action name of event (turn off grid, stop charging, move to battery, etc.)
  action: BlackoutAction = BlackoutAction.empty
  # True if event force finish requested
  # Actual for current active event only
  force_finish: bool = False
  # True if event force stop requested
  # Actual for current active event only
  force_stop: bool = False
  # Next stage name of event processing
  # Actual for current active event only
  next_stage: BlackoutStage = BlackoutStage.stage1

  class Config(BaseConfig):
    # Apply strategies to specific types in this class
    serialization_strategy = {
      datetime: MyDateTimeStrategy(),
      BlackoutAction: SchedulerActionStrategy(),
      BlackoutStage: SchedulerStageStrategy(),
    }
