from dataclasses import dataclass

from blackout_event_stage import BlackoutEventStage
from blackout_scheduled_event import BlackoutScheduledEvent

@dataclass
class BlackoutCurrentEvent(BlackoutScheduledEvent):
  # Next stage name of event processing
  # Actual for current active event only
  stage: BlackoutEventStage
  # True if event force finish requested
  # Actual for current active event only
  force_finish: bool = False
  # True if event force stop requested
  # Actual for current active event only
  force_stop: bool = False
