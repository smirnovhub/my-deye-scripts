from typing import List
from datetime import date

from dataclasses import dataclass, field
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class CurrentLimitConfigDto(DataClassJSONMixin):
  """
  Data transfer object representing the static configuration for current limit
  """
  battery_charge_lost_coef: float = 2.0
  dont_regulate_dates: List[date] = field(default_factory = list)
