from typing import List
from dataclasses import dataclass

from deye_graph_data import DeyeGraphData

@dataclass
class DeyeGraphInverterData:
  inverter: str
  graphs: List[DeyeGraphData]
