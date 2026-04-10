from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class DeyeGraphData(DataClassJSONMixin):
  group: str
  name: str
  description: str
