from typing import List
from datetime import date

from dataclasses import dataclass, field
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class CurrentLimitConfigDto(DataClassJSONMixin):
  """
  Data transfer object representing the static configuration for current limit
  """
  SELECTION_VALUES_KEY = "selection_values"
  ROW_LENGTH_KEY = "row_length"

  max_charge_current: int = field(
    default = 60,
    metadata = {
      SELECTION_VALUES_KEY: [45, 50, 55, 60, 65, 70, 75, 80],
      ROW_LENGTH_KEY: 4,
    },
  )

  charge_force_coef: float = field(
    default = 2.0,
    metadata = {
      SELECTION_VALUES_KEY: [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
      ROW_LENGTH_KEY: 4,
    },
  )

  days_between_full_charge: int = field(
    default = 15,
    metadata = {
      SELECTION_VALUES_KEY: [7, 10, 15, 20, 25, 30],
      ROW_LENGTH_KEY: 3,
    },
  )

  stop_charge_current: int = 0
  dont_regulate_dates: List[date] = field(default_factory = list)
