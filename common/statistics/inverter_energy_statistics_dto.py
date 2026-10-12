from typing import Dict
from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin
from energy_statistics_dto import EnergyStatisticsDto

@dataclass
class InverterEnergyStatisticsDto(DataClassJSONMixin):
  """Data transfer object representing aggregated energy statistics across all inverters."""
  energy_statistics: Dict[str, EnergyStatisticsDto]
