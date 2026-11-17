from typing import List
from datetime import date, datetime

from dataclasses import dataclass, field
from mashumaro.mixins.json import DataClassJSONMixin

from current_limit_config_group import CurrentLimitConfigGroup

@dataclass
class CurrentLimitConfigDto(DataClassJSONMixin):
  """
  Data transfer object representing the static configuration for current limit
  """
  SELECTION_VALUES_KEY = "selection_values"
  SELECTION_GROUP_KEY = "selection_group"

  max_charge_current: int = field(
    default = 60,
    metadata = {
      SELECTION_VALUES_KEY: [
        [45, 50, 55, 60],
        [65, 70, 75, 80],
      ],
      SELECTION_GROUP_KEY: CurrentLimitConfigGroup.charging,
    },
  )

  stop_charge_current: int = field(
    default = 0,
    metadata = {
      SELECTION_VALUES_KEY: [
        [0, 1, 2, 3],
      ],
      SELECTION_GROUP_KEY: CurrentLimitConfigGroup.charging,
    },
  )

  charge_force_coef: float = field(
    default = 2.0,
    metadata = {
      SELECTION_VALUES_KEY: [
        [1.5, 2.0, 2.5, 3.0],
        [3.5, 4.0, 4.5, 5.0],
      ],
      SELECTION_GROUP_KEY: CurrentLimitConfigGroup.charging,
    },
  )

  days_between_full_charge: int = field(
    default = 15,
    metadata = {
      SELECTION_VALUES_KEY: [
        [7, 10, 15],
        [20, 25, 30],
      ],
      SELECTION_GROUP_KEY: CurrentLimitConfigGroup.charging,
    },
  )

  winter_start_month: int = field(
    default = 11,
    metadata = {
      SELECTION_VALUES_KEY: [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
      ],
      SELECTION_GROUP_KEY: CurrentLimitConfigGroup.winter,
    },
  )

  winter_start_day: int = field(
    default = 15,
    metadata = {
      SELECTION_VALUES_KEY: [
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 10],
        [11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20],
        [21, 22, 23, 24, 25],
        [26, 27, 28, 29, 30],
      ],
      SELECTION_GROUP_KEY:
      CurrentLimitConfigGroup.winter,
    },
  )

  winter_end_month: int = field(
    default = 3,
    metadata = {
      SELECTION_VALUES_KEY: [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
      ],
      SELECTION_GROUP_KEY: CurrentLimitConfigGroup.winter,
    },
  )

  winter_end_day: int = field(
    default = 1,
    metadata = {
      SELECTION_VALUES_KEY: [
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 10],
        [11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20],
        [21, 22, 23, 24, 25],
        [26, 27, 28, 29, 30],
      ],
      SELECTION_GROUP_KEY:
      CurrentLimitConfigGroup.winter,
    },
  )

  dont_regulate_dates: List[date] = field(default_factory = list)

  def validate(self) -> None:
    # Validate dates to catch invalid days like Feb 31
    try:
      date(1999, self.winter_start_month, self.winter_start_day)
    except ValueError as e:
      raise ValueError(f"Invalid winter start date: {e}") from e

    try:
      date(1999, self.winter_end_month, self.winter_end_day)
    except ValueError as ee:
      raise ValueError(f"Invalid winter end date: {ee}") from ee

  @property
  def is_winter(self) -> bool:
    # Get current date as a (month, day) tuple
    now = datetime.now()
    current = (now.month, now.day)

    start = (self.winter_start_month, self.winter_start_day)
    end = (self.winter_end_month, self.winter_end_day)

    if start <= end:
      # Normal case (e.g., within one calendar year)
      return start <= current < end

    # Cross-year case (e.g., Nov 15 to Mar 1)
    return current >= start or current < end

  @property
  def do_not_regulate(self) -> bool:
    return date.today() in self.dont_regulate_dates
