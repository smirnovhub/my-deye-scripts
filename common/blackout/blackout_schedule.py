from typing import List

from copy import deepcopy
from datetime import datetime
from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

from blackout_scheduled_event import BlackoutScheduledEvent

@dataclass
class BlackoutSchedule(DataClassJSONMixin):
  events: List[BlackoutScheduledEvent]

  def __post_init__(self):
    # Sort events by date after object creation
    self.events.sort(key = lambda x: x.date)

  def get_upcoming_events(self) -> 'BlackoutSchedule':
    """
    Returns a sorted list of events scheduled for the future
    """
    events = sorted(
      [event for event in self.events if event.date > datetime.now()],
      key = lambda x: x.date,
    )

    return BlackoutSchedule(events = events)

  def get_only_unique_events(self) -> 'BlackoutSchedule':
    """
    Returns a new BlackoutSchedule instance with unique events by date.
    """
    # Dictionary uses date as key, effectively keeping only the last occurrence
    # or the first one depending on how you populate it.
    unique_map = {event.date: event for event in self.events}

    # Create a new list from dictionary values and sort it
    sorted_events = sorted(unique_map.values(), key = lambda x: x.date)

    # Return a new instance to avoid side effects
    return BlackoutSchedule(events = deepcopy(sorted_events))
