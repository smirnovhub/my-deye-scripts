from typing import List
from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class BlackoutEventExtraData(DataClassJSONMixin):
  # Stored time of use socs
  time_of_use_socs: List[int] = []
  # Stored time of use powers
  time_of_use_powers: List[int] = []
