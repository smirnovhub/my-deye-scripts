from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class EnergyStatisticsDto(DataClassJSONMixin):
  """
  Data transfer object representing the configuration for energy statistics.
  """
  inverter: str
  consumption: float
  production_pv1: float
  production_pv2: float
  gen_energy: float
