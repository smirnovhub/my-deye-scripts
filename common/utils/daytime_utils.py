from suntime import Sun
from typing import Optional
from datetime import datetime, timedelta

class DayTimeUtils:
  """
  Utility class for calculating sunrise, sunset, and day/night status
  based on GPS coordinates.

  Uses the Sun class (assumed to provide get_sunrise_time() and get_sunset_time())
  and GpsCoordinates for the observer's location.
  """
  def __init__(self, latitude: float, longitude: float):
    self._sun = Sun(latitude, longitude)

  @property
  def sunrise_time(self) -> datetime:
    """
    Get the sunrise time as a datetime object.

    Returns:
        datetime: The calculated sunrise time.
    """
    return self._sun.get_sunrise_time()

  @property
  def sunset_time(self) -> datetime:
    """
    Get the sunset time as a datetime object.

    Returns:
        datetime: The calculated sunset time.
    """
    return self._sun.get_sunset_time()

  @property
  def sunrise_timestamp(self) -> float:
    """
    Get the timestamp of the next sunrise at the current GPS location.

    Returns:
        float: Sunrise time as a Unix timestamp.
    """
    return self._sun.get_sunrise_time().timestamp()

  @property
  def sunset_timestamp(self) -> float:
    """
    Get the timestamp of the next sunset at the current GPS location.

    Returns:
        float: Sunset time as a Unix timestamp.
    """
    return self._sun.get_sunset_time().timestamp()

  def is_sun_risen(self, shift: Optional[timedelta] = None) -> bool:
    """
    Check if the sun has already risen, optionally applying a time shift.

    Args:
        shift (Optional[timedelta]): Shift the sunrise time by this delta.
            - Positive: sunrise is considered later.
            - Negative: sunrise is considered earlier.

    Returns:
        bool: True if the sun has risen, False otherwise.
    """
    actual_shift = shift if shift is not None else timedelta()
    return datetime.now() >= (self.sunrise_time + actual_shift)

  def is_sun_set(self, shift: Optional[timedelta] = None) -> bool:
    """
    Check if the sun has already set, optionally applying a time shift.

    Args:
        shift (Optional[timedelta]): Shift the sunset time by this delta.
            - Positive: sunset is considered later.
            - Negative: sunset is considered earlier.

    Returns:
        bool: True if the sun has set, False otherwise.
    """
    actual_shift = shift if shift is not None else timedelta()
    return datetime.now() >= (self.sunset_time + actual_shift)

  def is_day_time(
    self,
    sunrise_shift: Optional[timedelta] = None,
    sunset_shift: Optional[timedelta] = None,
  ) -> bool:
    """
    Determine if it is currently daytime at the GPS location, optionally
    applying shifts to sunrise and sunset times.

    Args:
        sunrise_shift (Optional[timedelta]): Shift sunrise time by this delta.
            - Positive: sunrise considered later.
            - Negative: sunrise considered earlier.
        sunset_shift (Optional[timedelta]): Shift sunset time by this delta.
            - Positive: sunset considered later.
            - Negative: sunset considered earlier.

    Returns:
        bool: True if it is daytime, False if it is night.
    """
    return self.is_sun_risen(sunrise_shift) and not self.is_sun_set(sunset_shift)
