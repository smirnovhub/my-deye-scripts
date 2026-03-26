from typing import List
from datetime import date
from dataclasses import dataclass

from deye_graph_inverter_data import DeyeGraphInverterData

@dataclass
class DeyeGraphInverters:
  graph_date: date
  inverters: List[DeyeGraphInverterData]
