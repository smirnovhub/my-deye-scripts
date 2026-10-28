from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class PrintableEnergyStatisticsRowDto(DataClassJSONMixin):
  label: str
  kw: float
  kwh: float
  percent: float
