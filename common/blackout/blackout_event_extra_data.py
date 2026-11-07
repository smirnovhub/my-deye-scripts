from typing import List
from dataclasses import dataclass, field
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class BlackoutEventExtraData(DataClassJSONMixin):
  # Stored time of use socs
  time_of_use_socs: List[int] = field(default_factory = list)
  # Stored time of use powers
  time_of_use_powers: List[int] = field(default_factory = list)
