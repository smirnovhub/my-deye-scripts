from typing import List
from dataclasses import dataclass

from deye_graph_data import DeyeGraphData
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class DeyeGraphGroupData(DataClassJSONMixin):
  group: str
  graphs: List[DeyeGraphData]
