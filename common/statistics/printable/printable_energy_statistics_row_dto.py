from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class PrintableEnergyStatisticsRowDto(DataClassJSONMixin):
  label: str
  kw: float
  kwh: float
  percent: float

  def __add__(self, other: 'PrintableEnergyStatisticsRowDto') -> 'PrintableEnergyStatisticsRowDto':
    return PrintableEnergyStatisticsRowDto(
      label = "Unlabeled Sum Dto",
      kw = self.kw + other.kw,
      kwh = self.kwh + other.kwh,
      percent = max(0.0, min(100.0, self.percent + other.percent)),
    )
