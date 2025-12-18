from typing import List

from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime, timedelta

from deye_exceptions import DeyeValueException

class BatteryForecastType(Enum):
  charge = auto()
  discharge = auto()

class BatteryForecastOrderType(Enum):
  by_percent = auto()
  by_time = auto()

@dataclass
class BatteryForecastItem:
  soc: int
  date: datetime

@dataclass
class BatteryForecastData:
  type: BatteryForecastType
  order_type: BatteryForecastOrderType
  items: List[BatteryForecastItem]

class BatteryForecastUtils:
  default_charge_lost_coef = 1.25
  forecast_lower_soc = 10

  charge_lost_coef_by_current = {
    1.3: 5,
    default_charge_lost_coef: 9999,
  }

  @staticmethod
  def get_forecast_by_percent(
    battery_soc: int,
    battery_capacity: int,
    battery_current: float,
    percent_step: int = 5,
  ) -> BatteryForecastData:
    if abs(battery_current) < 0.1:
      raise DeyeValueException('Battery is in idle mode')

    if battery_current > 0:
      return BatteryForecastUtils.get_discharge_forecast_by_percent(
        battery_soc,
        battery_capacity,
        battery_current,
        percent_step,
      )
    else:
      return BatteryForecastUtils.get_charge_forecast_by_percent(
        battery_soc,
        battery_capacity,
        battery_current,
        percent_step,
      )

  @staticmethod
  def get_forecast_by_time(
    battery_soc: int,
    battery_capacity: int,
    battery_current: float,
    max_items: int = 25,
  ) -> BatteryForecastData:
    if abs(battery_current) < 0.1:
      raise DeyeValueException('Battery is in idle mode')

    def get_forecast(step_timedelta: timedelta, skip_duplicated_soc: bool = False) -> BatteryForecastData:
      if battery_current > 0:
        return BatteryForecastUtils.get_discharge_forecast_by_time(
          battery_soc = battery_soc,
          battery_capacity = battery_capacity,
          battery_current = battery_current,
          step_timedelta = step_timedelta,
          max_items = max_items + 3,
          skip_duplicated_soc = skip_duplicated_soc,
        )
      else:
        return BatteryForecastUtils.get_charge_forecast_by_time(
          battery_soc = battery_soc,
          battery_capacity = battery_capacity,
          battery_current = battery_current,
          step_timedelta = step_timedelta,
          max_items = max_items + 3,
          skip_duplicated_soc = skip_duplicated_soc,
        )

    steps = {
      5: False,
      10: False,
      15: False,
      30: False,
      60: True,
    }

    for step, skip in steps.items():
      items = get_forecast(timedelta(minutes = step), skip)
      if len(items.items) <= max_items:
        return items

    return BatteryForecastData(
      type = items.type,
      order_type = items.order_type,
      items = items.items[:max_items - 1] + [items.items[-1]],
    )

  ############ BY PERCENT ############

  @staticmethod
  def get_charge_forecast_by_percent(
    battery_soc: int,
    battery_capacity: int,
    battery_current: float,
    percent_step: int = 5,
  ) -> BatteryForecastData:
    if abs(battery_current) < 0.1:
      raise DeyeValueException('Battery is in idle mode')

    if battery_current > 0:
      raise DeyeValueException('Battery is discharging')

    soc = battery_soc - battery_soc % percent_step

    if soc >= 100:
      raise DeyeValueException('Battery is fully charged')

    items: List[BatteryForecastItem] = []

    charge_lost_coef = BatteryForecastUtils.get_charge_lost_coef(battery_current)

    while True:
      soc += percent_step

      if soc > 100:
        break

      if soc <= battery_soc:
        continue

      soc_delta = soc - battery_soc

      capacity = battery_capacity * (soc_delta / 100) * charge_lost_coef
      hours_to_soc = abs(capacity / battery_current)
      soc_date = datetime.now() + timedelta(hours = hours_to_soc)

      items.append(BatteryForecastItem(
        soc = round(soc),
        date = soc_date,
      ))

    return BatteryForecastData(
      type = BatteryForecastType.charge,
      order_type = BatteryForecastOrderType.by_percent,
      items = items,
    )

  @staticmethod
  def get_discharge_forecast_by_percent(
    battery_soc: int,
    battery_capacity: int,
    battery_current: float,
    percent_step: int = 5,
  ) -> BatteryForecastData:
    # For tests
    if battery_soc > 100:
      raise DeyeValueException('Battery is overcharged')

    if abs(battery_current) < 0.1:
      raise DeyeValueException('Battery is in idle mode')

    if battery_current < 0:
      raise DeyeValueException('Battery is charging')

    items: List[BatteryForecastItem] = []

    soc = battery_soc - battery_soc % percent_step

    if soc == battery_soc:
      soc -= percent_step

    while soc >= BatteryForecastUtils.forecast_lower_soc:
      soc_delta = battery_soc - soc
      capacity = battery_capacity * (soc_delta / 100)
      hours_to_soc = abs(capacity / battery_current)
      soc_date = datetime.now() + timedelta(hours = hours_to_soc)

      items.append(BatteryForecastItem(
        soc = round(soc),
        date = soc_date,
      ))

      soc -= percent_step

    return BatteryForecastData(
      type = BatteryForecastType.discharge,
      order_type = BatteryForecastOrderType.by_percent,
      items = items,
    )

  ############ BY TIME ############

  @staticmethod
  def get_charge_forecast_by_time(
    battery_soc: int,
    battery_capacity: int,
    battery_current: float,
    step_timedelta: timedelta,
    max_items: int,
    skip_duplicated_soc: bool = False,
  ) -> BatteryForecastData:
    if abs(battery_current) < 0.1:
      raise DeyeValueException('Battery is in idle mode')

    if battery_current > 0:
      raise DeyeValueException('Battery is discharging')

    if battery_soc >= 100:
      raise DeyeValueException('Battery is fully charged')

    items: List[BatteryForecastItem] = []

    now = datetime.now()

    # align start time upward
    step_seconds = step_timedelta.total_seconds()
    now_seconds = now.timestamp()
    remainder = now_seconds % step_seconds

    charge_lost_coef = BatteryForecastUtils.get_charge_lost_coef(battery_current)

    if remainder == 0:
      aligned_seconds = now_seconds
    else:
      aligned_seconds = now_seconds + (step_seconds - remainder)

    t = datetime.fromtimestamp(aligned_seconds)

    while True:
      # how many hours from now
      hours_passed = (t - now).total_seconds() / 3600.0

      # charged energy (kWh), negative current because charging
      charged = hours_passed * abs(battery_current)

      # convert charged energy to SOC
      # capacity[percent] = energy[kWh] / battery_capacity * 100
      soc_gain = (charged / battery_capacity) * 100.0

      # account for charge inefficiency
      soc_gain = soc_gain / charge_lost_coef

      forecast_soc = battery_soc + soc_gain

      if forecast_soc > 100:
        break

      soc = round(forecast_soc)

      if skip_duplicated_soc and items and soc == items[-1].soc:
        t += step_timedelta
        continue

      items.append(BatteryForecastItem(
        soc = soc,
        date = t,
      ))

      if len(items) > max_items:
        break

      t += step_timedelta

    # add final 100% element if last SOC < 100
    last_soc = items[-1].soc if items else battery_soc
    if last_soc < 100:
      remaining_soc = 100 - battery_soc
      hours_needed = (remaining_soc * charge_lost_coef * battery_capacity) / (100.0 * abs(battery_current))
      final_time = now + timedelta(hours = hours_needed)
      items.append(BatteryForecastItem(
        soc = 100,
        date = final_time,
      ))

    return BatteryForecastData(
      type = BatteryForecastType.charge,
      order_type = BatteryForecastOrderType.by_time,
      items = items,
    )

  @staticmethod
  def get_discharge_forecast_by_time(
    battery_soc: int,
    battery_capacity: int,
    battery_current: float,
    step_timedelta: timedelta,
    max_items: int,
    skip_duplicated_soc: bool = False,
  ) -> BatteryForecastData:
    # For tests
    if battery_soc > 100:
      raise DeyeValueException('Battery is overcharged')

    if abs(battery_current) < 0.1:
      raise DeyeValueException('Battery is in idle mode')

    if battery_current < 0:
      raise DeyeValueException('Battery is charging')

    items: List[BatteryForecastItem] = []

    now = datetime.now()

    # align "t" upward to this step
    step_seconds = step_timedelta.total_seconds()
    now_seconds = now.timestamp()
    remainder = now_seconds % step_seconds

    if remainder == 0:
      aligned_seconds = now_seconds
    else:
      aligned_seconds = now_seconds + (step_seconds - remainder)

    t = datetime.fromtimestamp(aligned_seconds)

    while True:
      hours_passed = (t - now).total_seconds() / 3600.0
      discharged = hours_passed * battery_current
      soc_drop = (discharged / battery_capacity) * 100.0
      forecast_soc = battery_soc - soc_drop

      if forecast_soc < BatteryForecastUtils.forecast_lower_soc:
        break

      soc = round(forecast_soc)

      if skip_duplicated_soc and items and soc == items[-1].soc:
        t += step_timedelta
        continue

      items.append(BatteryForecastItem(
        soc = soc,
        date = t,
      ))

      if len(items) > max_items:
        break

      t += step_timedelta

    # add final soc element if last SOC > forecast_lower_soc
    if items[-1].soc > BatteryForecastUtils.forecast_lower_soc:
      soc_delta = battery_soc - BatteryForecastUtils.forecast_lower_soc
      capacity = battery_capacity * (soc_delta / 100.0)

      # calculate exact hours to reach final soc
      hours_to_soc = abs(capacity / battery_current)

      # exact datetime for final soc
      soc_date = datetime.now() + timedelta(hours = hours_to_soc)

      # append the final soc point
      items.append(BatteryForecastItem(
        soc = BatteryForecastUtils.forecast_lower_soc,
        date = soc_date,
      ))

    return BatteryForecastData(
      type = BatteryForecastType.discharge,
      order_type = BatteryForecastOrderType.by_time,
      items = items,
    )

  @staticmethod
  def get_charge_lost_coef(battery_current: float) -> float:
    battery_current = abs(battery_current)
    for coef, current in BatteryForecastUtils.charge_lost_coef_by_current.items():
      if battery_current <= current:
        print(f'COEF = {coef}')
        return coef
    return BatteryForecastUtils.default_charge_lost_coef
