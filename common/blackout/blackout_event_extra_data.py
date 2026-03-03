from dataclasses import dataclass
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class BlackoutEventExtraData(DataClassJSONMixin):
  # Stored battery SOC
  time_of_use_soc: int = 0
  # Stored time of use power
  time_of_use_power: int = 0
