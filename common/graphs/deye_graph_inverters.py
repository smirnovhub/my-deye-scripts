from typing import List
from datetime import date
from dataclasses import dataclass

from deye_graph_inverter_data import DeyeGraphInverterData
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class DeyeGraphInverters(DataClassJSONMixin):
  graph_date: date
  inverters: List[DeyeGraphInverterData]
