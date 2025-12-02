from suntime import Sun
from datetime import datetime

class DayTimeUtils:
  """
  Utility class for calculating sunrise, sunset, and day/night status
  based on GPS coordinates.

  Uses the Sun class (assumed to provide get_sunrise_time() and get_sunset_time())
  and GpsCoordinates for the observer's location.
  """
  def __init__(self, latitude: float, longitude: float):
    self.sun = Sun(latitude, longitude)

  @property
  def sunrise_timestamp(self) -> float:
    """
    Get the timestamp of the next sunrise at the current GPS location.

    Returns:
        float: Sunrise time as a Unix timestamp.
    """
    return self.sun.get_sunrise_time().timestamp()

  @property
  def sunset_timestamp(self) -> float:
    """
    Get the timestamp of the next sunset at the current GPS location.

    Returns:
        float: Sunset time as a Unix timestamp.
    """
    return self.sun.get_sunset_time().timestamp()

  def is_sun_risen(self, shift_seconds: float = 0) -> bool:
    """
    Check if the sun has already risen, optionally applying a time shift.

    Args:
        shift_seconds (float): Shift the current time by this many seconds.
            - Positive: check as if the current time is later.
            - Negative: check as if the current time is earlier.

    Returns:
        bool: True if the sun has risen, False otherwise.
    """
    return (datetime.now().timestamp() + shift_seconds) >= self.sunrise_timestamp

  def is_sun_set(self, shift_seconds: float = 0) -> bool:
    """
    Check if the sun has already set, optionally applying a time shift.

    Args:
        shift_seconds (float): Shift the current time by this many seconds.
            - Positive: check as if the current time is later.
            - Negative: check as if the current time is earlier.

    Returns:
        bool: True if the sun has set, False otherwise.
    """
    return (datetime.now().timestamp() + shift_seconds) >= self.sunset_timestamp

  def is_day_time(self, sunrise_shift_hours: float = 0, sunset_shift_hours: float = 0) -> bool:
    """
    Determine if it is currently daytime at the GPS location, optionally
    applying shifts to sunrise and sunset times.

    Args:
        sunrise_shift_hours (float): Shift sunrise time by this many hours.
            - Positive: sunrise considered later.
            - Negative: sunrise considered earlier.
        sunset_shift_hours (float): Shift sunset time by this many hours.
            - Positive: sunset considered later.
            - Negative: sunset considered earlier.

    Returns:
        bool: True if it is daytime, False if it is night.
    """
    return self.is_sun_risen(sunrise_shift_hours * 3600) and not self.is_sun_set(sunset_shift_hours * 3600)
