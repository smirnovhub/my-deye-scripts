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

  def get_upcoming_events(self, max_expired_events: int = 0) -> 'BlackoutSchedule':
    """
    Returns all future events and up to N most recent past events
    """
    now = datetime.now()

    # Split events into future and past categories
    future_events = [e for e in self.events if e.date > now]
    past_events = [e for e in self.events if e.date <= now]

    # Sort past events by date descending to pick the N latest ones
    past_events.sort(key = lambda x: x.date, reverse = True)
    recent_past = past_events[:max_expired_events]

    # Combine and sort the final result chronologically
    combined = sorted(future_events + recent_past, key = lambda x: x.date)

    return BlackoutSchedule(events = combined)

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
