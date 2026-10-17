from dataclasses import dataclass
from base_websocket_message import BaseWebsocketMessage

# Specific message subclass for generic updates
@dataclass
class SchedulerGenericUpdateMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "generic_update"
  type: str = MESSAGE_TYPE

# Specific message subclass for adding an event
@dataclass
class SchedulerEventAddMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_add"
  type: str = MESSAGE_TYPE

# Specific message subclass for removing an event
@dataclass
class SchedulerEventRemoveMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_remove"
  type: str = MESSAGE_TYPE

# Specific message subclass for clearing the schedule
@dataclass
class SchedulerClearMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "schedule_clear"
  type: str = MESSAGE_TYPE

# Specific message subclass for forcing an event finish request
@dataclass
class SchedulerEventForceFinishRequestMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_force_finish_request"
  type: str = MESSAGE_TYPE

# Specific message subclass for forcing an event stop request
@dataclass
class SchedulerEventForceStopRequestMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_force_stop_request"
  type: str = MESSAGE_TYPE

# Specific message subclass for tracking event stage changes
@dataclass
class SchedulerEventStageChangeMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_stage_change"
  type: str = MESSAGE_TYPE

# Specific message subclass for event start
@dataclass
class SchedulerEventStartMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_start"
  type: str = MESSAGE_TYPE

# Specific message subclass for event completion
@dataclass
class SchedulerEventCancelMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_cancel"
  type: str = MESSAGE_TYPE

# Specific message subclass for event completion
@dataclass
class SchedulerEventDoneMessage(BaseWebsocketMessage):
  MESSAGE_TYPE = "event_done"
  type: str = MESSAGE_TYPE

# Registry mapping message types to their respective classes
SCHEDULER_MESSAGE_TYPE_REGISTRY = {
  SchedulerGenericUpdateMessage.MESSAGE_TYPE: SchedulerGenericUpdateMessage,
  SchedulerEventAddMessage.MESSAGE_TYPE: SchedulerEventAddMessage,
  SchedulerEventRemoveMessage.MESSAGE_TYPE: SchedulerEventRemoveMessage,
  SchedulerClearMessage.MESSAGE_TYPE: SchedulerClearMessage,
  SchedulerEventForceFinishRequestMessage.MESSAGE_TYPE: SchedulerEventForceFinishRequestMessage,
  SchedulerEventForceStopRequestMessage.MESSAGE_TYPE: SchedulerEventForceStopRequestMessage,
  SchedulerEventStageChangeMessage.MESSAGE_TYPE: SchedulerEventStageChangeMessage,
  SchedulerEventStartMessage.MESSAGE_TYPE: SchedulerEventStartMessage,
  SchedulerEventCancelMessage.MESSAGE_TYPE: SchedulerEventCancelMessage,
  SchedulerEventDoneMessage.MESSAGE_TYPE: SchedulerEventDoneMessage,
}
