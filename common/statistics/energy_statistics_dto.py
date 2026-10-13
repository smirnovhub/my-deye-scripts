from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class EnergyStatisticsDto(DataClassJSONMixin):
  """Data transfer object representing energy statistics for a single inverter."""
  consumption: float
  production_pv1: float
  production_pv2: float
  gen_energy: float
