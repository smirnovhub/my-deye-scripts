from dataclasses import dataclass
from typing import List
from mashumaro.mixins.json import DataClassJSONMixin
from printable_energy_statistics_row_dto import PrintableEnergyStatisticsRowDto

@dataclass
class PrintableEnergyStatisticsDto(DataClassJSONMixin):
  printable_statistics: List[PrintableEnergyStatisticsRowDto]
