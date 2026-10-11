from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class PvProductionDto(DataClassJSONMixin):
  """
  Data transfer object representing the configuration for PV production
  """
  master_pv1: float
  master_pv2: float
  master_gen: float
  slave1_pv1: float
  slave1_pv2: float
  slave1_gen: float
