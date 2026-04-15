from typing import List
from dataclasses import dataclass

from deye_graph_group_data import DeyeGraphGroupData
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class DeyeGraphInverterData(DataClassJSONMixin):
  inverter: str
  groups: List[DeyeGraphGroupData]
