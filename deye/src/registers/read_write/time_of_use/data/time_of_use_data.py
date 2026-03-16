import json

from dataclasses import dataclass, asdict

from time_of_use_weeks import TimeOfUseWeeks
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
  weeks: TimeOfUseWeeks

  @property
  def week(self) -> TimeOfUseWeek:
    if not self.weeks.values:
      raise RuntimeError("Time of Use weeks values are empty")
    return self.weeks.values[0]

  def check_bounds(self):
    items_count = 6

    self.charges.check_bounds(items_count = items_count)
    self.times.check_bounds(items_count = items_count)
    self.powers.check_bounds(items_count = items_count)
    self.socs.check_bounds(items_count = items_count)
    self.weeks.check_bounds(items_count = 1)

  def check_power(self, max_power: int):
    self.powers.check_power(max_power = max_power)

  def check_soc(self, min_soc: int):
    self.socs.check_soc(min_soc = min_soc)

  def check_time(self) -> None:
    self.times.check_time()

  def __str__(self):
    # Compact JSON in a single line
    return json.dumps(asdict(self), ensure_ascii = False)
