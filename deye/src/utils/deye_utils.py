import os
import re
import queue
import struct
import requests

from typing import Union, List
from datetime import datetime, timedelta
from pysolarmanv5 import NoSocketAvailableError

from deye_exceptions import (
  DeyeConnectionErrorException,
  DeyeKnownException,
  DeyeNoSocketAvailableException,
  DeyeOSErrorException,
  DeyeQueueIsEmptyException,
  DeyeUnknownException,
  DeyeValueException,
)

class DeyeUtils:
  time_format_str = '%Y-%m-%d %H:%M:%S'

  # some code is based on githubDante / deye-controller
  # https://github.com/githubDante/deye-controller
  @staticmethod
  def from_long_register_values(values: List[int], scale: int) -> float:
    value = DeyeUtils.to_unsigned_bytes(values[::-1])
    return int.from_bytes(value, byteorder = 'big') / scale

  @staticmethod
  def to_long_register_values(val: float, scale: int, register_count: int) -> List[int]:
    # Convert the float value into a scaled integer (e.g. 123.45 * 100 = 12345)
    scaled = int(round(val * scale))

    # Each register is 2 bytes → total length in bytes = register_count * 2
    byte_length = register_count * 2

    # Convert the scaled integer into bytes in big-endian order
    b = scaled.to_bytes(byte_length, byteorder = 'big')

    # Split the byte sequence into 16-bit (2-byte) registers
    regs = [int.from_bytes(b[i:i + 2], byteorder = 'big') for i in range(0, byte_length, 2)]

    # Reverse the order, because from_long_register_values() expects reversed registers
    return regs[::-1]

  # Convert PDU integer or list with integers to bytes (signed)
  # It's needed for a bunch of Deye registers (SN, Time, etc.)
  @staticmethod
  def to_signed(val: int) -> int:
    return struct.unpack('>h', struct.pack('>H', val))[0]

  @staticmethod
  def to_unsigned(val: int) -> int:
    return struct.unpack('>H', struct.pack('>h', val))[0]

  # Convert PDU integer or list with integers to bytes (signed)
  # It's needed for a bunch of Deye registers (SN, Time, etc.)
  @staticmethod
  def to_bytes(val: Union[int, List[int]]):
    if isinstance(val, List):
      return bytes.fromhex(''.join([struct.pack('>h', x).hex() for x in val]))
    elif isinstance(val, int):
      return struct.pack('>h', val)
    else:
      raise DeyeValueException(f'to_bytes(): not int / List[int]: {str(val)}')

  # Convert PDU integer(s) to byte(s)
  # Needed for registers marked with Wh/Wh_high/Wh_low in the Modbus documentation
  @staticmethod
  def to_unsigned_bytes(val: Union[int, List[int]]) -> bytes:
    if isinstance(val, List):
      return bytes.fromhex(''.join([struct.pack('>H', x).hex() for x in val]))
    elif isinstance(val, int):
      return struct.pack('>H', val)
    else:
      raise DeyeValueException(f'to_unsigned_bytes(): not int / List[int]: {str(val)}')

  # Convert a sequence of integers (Year, Month, Date, Hour, Minute, Second)
  # to 3 bytes tuple suitable for writing though pysolarman
  @staticmethod
  def to_inv_time(vals: List[int]) -> List[int]:
    return list(struct.unpack('>hhh', struct.pack('>bbbbbb', *vals)))

  @staticmethod
  def format_end_date(date: datetime) -> str:
    """
    Format a datetime object as a human-readable string with 'today', 'tomorrow', 
    or a full date.

    The function compares the given date to the current date and the next day:
      - If the date is today, returns "today, HH:MM".
      - If the date is tomorrow, returns "tomorrow, HH:MM".
      - Otherwise, returns "YYYY-MM-DD, HH:MM".

    Args:
        date (datetime): The datetime object to format.

    Returns:
        str: Formatted string representing the date and time.
    """
    today = datetime.now()
    tomorrow = today + timedelta(days = 1)

    date_day = date.date()
    today_day = today.date()
    tomorrow_day = tomorrow.date()

    time_str = date.strftime('%H:%M')

    if date_day == today_day:
      return f"today, {time_str}"
    if date_day == tomorrow_day:
      return f"tomorrow, {time_str}"
    return date.strftime('%Y-%m-%d, %H:%M')

  @staticmethod
  def custom_round(value: float, digits: int = 2) -> str:
    """
    Round a floating-point number to a specified number of decimal places and return
    it as a cleaned string without unnecessary trailing zeros or a trailing dot.

    Steps:
    1. Round the input value to `digits` decimal places.
    2. Convert the rounded value to a string with exactly `digits` decimal places.
    3. Remove trailing zeros and a trailing decimal point if they become redundant.

    Examples:
        custom_round(3.14159, 2) -> "3.14"
        custom_round(2.0, 2)     -> "2"
        custom_round(2.500, 2)   -> "2.5"
        custom_round(7.0, 0)     -> "7"

    Args:
        value (float): The number to round and format.
        digits (int): Number of decimal places to preserve before cleanup.

    Returns:
        str: The formatted number without unnecessary trailing zeros or a final dot.
    """
    # Round the number to the specified number of decimal places
    rounded = round(value, digits)

    # No decimal part required — simply return integer-like string
    if digits == 0:
      return str(int(rounded))

    # Convert to string with fixed decimal places
    s = f"{rounded:.{digits}f}"

    # Strip trailing zeros and a trailing dot if present
    return s.rstrip("0").rstrip(".")

  @staticmethod
  def format_timedelta(td: timedelta, add_seconds: bool = False) -> str:
    """
    Convert a timedelta object into a compact human-readable string such as
    '2h 5m' or '1d 3h'.

    The function automatically handles rollover conversions like 60s → 1m,
    60m → 1h, 24h → 1d, etc. Negative durations are prefixed with a minus sign.

    Args:
        td (timedelta): The time difference to format.
        add_seconds (bool): If True, include seconds in the output even when
            higher units (minutes, hours, etc.) are present.

    Returns:
        str: A short formatted representation of the time delta.
    """
    seconds = int(td.total_seconds())
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)

    if seconds < 1:
      return "0s"

    # Time units in descending order
    periods = [
      (" year", 60 * 60 * 24 * 365),
      (" month", 60 * 60 * 24 * 30),
      ("d", 60 * 60 * 24),
      ("h", 60 * 60),
      ("m", 60),
      ("s", 1),
    ]

    # Always include seconds if add_seconds=True, otherwise skip later
    strings = []
    for name, length in periods:
      if seconds >= length:
        value, seconds = divmod(seconds, length)
        if name == "s" and not add_seconds:
          # Skip seconds unless requested
          continue
        strings.append(f"{value}{name}")

    # If we ended up with "60s" -> handle as "1m"
    # Actually handled already by divmod() above due to integer division.
    return sign + " ".join(strings)

  # Ensure that the specified directory exists
  # If it does not exist, create it (including all intermediate directories)
  # and apply the specified permissions (mode)
  @staticmethod
  def ensure_dir_exists(path, mode = 0o755):
    # Create all parent directories if they do not exist
    if not os.path.exists(path):
      os.makedirs(path, exist_ok = True)
      os.chmod(path, mode)

  # Ensure that the specified file exists
  # If it does not exist, create an empty fil
  # and apply the specified permissions (mode)
  @staticmethod
  def ensure_file_exists(path, mode = 0o644):
    # Create the file itself if it does not exist
    if not os.path.exists(path):
      open(path, 'w').close()
      os.chmod(path, mode)

  # Ensure that both the parent directory and the file exist
  # If the directory does not exist, create it with dir_mode
  # If the file does not exist, create it with file_mode
  @staticmethod
  def ensure_dir_and_file_exists(path, dir_mode = 0o755, file_mode = 0o644):
    dir_path = os.path.dirname(path)
    DeyeUtils.ensure_dir_exists(dir_path, dir_mode)
    DeyeUtils.ensure_file_exists(path, file_mode)

  @staticmethod
  def get_reraised_exception(exception: Exception, message: str) -> Exception:
    if isinstance(exception, DeyeKnownException):
      return exception

    try:
      raise exception
    except queue.Empty:
      return DeyeQueueIsEmptyException(f'{message}: Queue is empty (get() timed out)')
    except NoSocketAvailableError as e:
      return DeyeNoSocketAvailableException(f'{message}: {e.__class__.__name__} ({str(e).strip(".")})')
    except requests.exceptions.Timeout:
      return DeyeConnectionErrorException(f'{message}: Connection timed out')
    except requests.exceptions.ConnectionError as e:
      text = DeyeUtils.get_exception_text(e)
      return DeyeConnectionErrorException(f'{message}: Connection error ({text})')
    except OSError as e:
      text = DeyeUtils.get_exception_text(e)
      return DeyeOSErrorException(f'{message}: OS error ({text})')
    except Exception as e:
      return DeyeUnknownException(f'{message}: {str(e)}')

  @staticmethod
  def get_exception_text(exc: OSError) -> str:
    if exc.errno and exc.strerror:
      return f'[Error {exc.errno}] {exc.strerror}'

    match = re.search(r"\[Errno -?\d+\][^')]+", str(exc))
    return match.group(0) if match else str(exc)

  @staticmethod
  def is_tests_on() -> bool:
    return os.getenv('TEST_RUN', '').strip().lower() == 'true'

  @staticmethod
  def turn_tests_on():
    os.environ['TEST_RUN'] = 'true'

  @staticmethod
  def get_test_retry_timeout() -> int:
    from deye_loggers import DeyeLoggers
    loggers = DeyeLoggers()
    return 5 + loggers.count * 2

  @staticmethod
  def get_current_time() -> datetime:
    return datetime(2017, 7, 25, 15, 33, 14) if DeyeUtils.is_tests_on() else datetime.now()
