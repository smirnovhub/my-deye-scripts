import json

from dataclasses import dataclass, asdict

from time_of_use_week import TimeOfUseWeek
from time_of_use_charges import TimeOfUseCharges
from time_of_use_powers import TimeOfUsePowers
from time_of_use_socs import TimeOfUseSocs
from time_of_use_times import TimeOfUseTimes

@dataclass
class TimeOfUseData:
  charges: TimeOfUseCharges
  times: TimeOfUseTimes
  powers: TimeOfUsePowers
  socs: TimeOfUseSocs
  weekly: TimeOfUseWeek

  def validate(self, min_soc: int, max_power: int):
    items_count = 6

    self.charges.validate(items_count = items_count)
    self.times.validate(items_count = items_count)
    self.powers.validate(items_count = items_count, max_power = max_power)
    self.socs.validate(items_count = items_count, min_soc = min_soc)

  def __str__(self):
    # Compact JSON in a single line
    return json.dumps(asdict(self), ensure_ascii = False)
