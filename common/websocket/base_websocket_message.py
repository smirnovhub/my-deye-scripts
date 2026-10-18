from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

# Base class for all WebSocket messages
@dataclass
class BaseWebsocketMessage(DataClassJSONMixin):
  type: str
