from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class DeyeGraphData(DataClassJSONMixin):
  name: str
  description: str
