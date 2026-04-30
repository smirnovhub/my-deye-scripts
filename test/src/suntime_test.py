#!/usr/bin/python3

import os
import sys
import unittest

from pathlib import Path
from datetime import datetime, timedelta

base_path = '../..'
current_path = Path(__file__).parent.resolve()
modules_path = (current_path / base_path / 'modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, [])

from suntime import Sun

class TestSunTimeLibrary(unittest.TestCase):
  def setUp(self):
    # Setting up coordinates for Kyiv and a fixed test date
    self.lat = 50.45
    self.lon = 30.52

    self.test_datetime = datetime(2026, 4, 30, 0, 0, 0)
    self.sun = Sun(self.lat, self.lon)

    # Constraints in hours
    self.min_day_hours = 7.5
    self.max_day_hours = 16.8

  def test_get_sunrise_time_with_datetime(self):
    # Testing if the method works with a datetime object (to avoid TypeError)
    try:
      sunrise = self.sun.get_sunrise_time(self.test_datetime)
      self.assertIsInstance(sunrise, datetime)
    except TypeError as e:
      self.fail(f"get_sunrise_time failed with datetime object: {e}")

  def test_sunrise_before_sunset(self):
    # Logic check: sunrise must always be before sunset on a normal day
    sunrise = self.sun.get_sunrise_time(self.test_datetime)
    sunset = self.sun.get_sunset_time(self.test_datetime)
    self.assertLess(sunrise, sunset, "Sunrise should occur before sunset")

  def test_output_is_utc_by_default(self):
    # Checking if the library returns naive UTC or properly flagged UTC
    sunrise = self.sun.get_sunrise_time(self.test_datetime)
    # If your library returns aware objects, tzinfo won't be None
    # If it returns naive, we check the values are within reasonable range
    self.assertTrue(2 <= sunrise.hour <= 3, f"Sunrise hour {sunrise.hour} is unusual for Kyiv in April")

  def test_different_latitudes(self):
    # Testing the library with southern hemisphere coordinates
    sydney_sun = Sun(-33.86, 151.20)
    sydney_date = datetime(2026, 4, 30, 0, 0)
    try:
      sunrise = sydney_sun.get_sunrise_time(sydney_date)
      self.assertIsInstance(sunrise, datetime)
    except Exception as e:
      self.fail(f"Failed to calculate for southern hemisphere: {e}")

  def test_invalid_coordinates(self):
    # Optional: testing how your library handles extreme values
    # Some versions might raise ValueError or return None
    extreme_sun = Sun(95, 200) # Invalid Lat/Lon
    with self.assertRaises(Exception):
      extreme_sun.get_sunrise_time(self.test_datetime)

  def test_sunrise_is_always_before_sunset(self):
    """
    Iterate through current year with steps.
    Ensure sunrise occurs before sunset for every single day.
    """
    year = datetime.now().year
    # Start of the year
    current_time = datetime(year, 1, 1, 0, 0, 0)
    # End of the year
    end_time = datetime(year, 12, 31, 23, 45, 0)
    interval = timedelta(minutes = 17, seconds = 7)

    while current_time <= end_time:
      try:
        # Get sunrise and sunset (these return UTC by default)
        sunrise = self.sun.get_sunrise_time(current_time)
        sunset = self.sun.get_sunset_time(current_time)

        # Calculate duration in hours
        day_duration = (sunset - sunrise).total_seconds() / 3600

        # Subtest allows the loop to continue even if one date fails
        with self.subTest(date = current_time):
          self.assertLess(
            sunrise,
            sunset,
            f"Logic Error at {current_time}: Sunrise {sunrise} >= Sunset {sunset}",
          )

          # Duration constraints check
          self.assertGreater(
            day_duration,
            self.min_day_hours,
            f"Day too short at {current_time.date()}: {day_duration:.2f} hours",
          )

          self.assertLess(
            day_duration,
            self.max_day_hours,
            f"Day too long at {current_time.date()}: {day_duration:.2f} hours",
          )

      except Exception as e:
        self.fail(f"Calculation failed at {current_time} with error: {e}")

      current_time += interval

if __name__ == '__main__':
  # Running with verbosity=2 for detailed output
  unittest.main(verbosity = 2)
