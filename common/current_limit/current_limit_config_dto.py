from typing import List
from datetime import date

from dataclasses import dataclass, field
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class CurrentLimitConfigDto(DataClassJSONMixin):
  """
  Data transfer object representing the static configuration for current limit
  """
  charge_force_coef: float = 2.0
  days_between_full_charge: int = 15
  dont_regulate_dates: List[date] = field(default_factory = list)
