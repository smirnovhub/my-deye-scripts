import os
import re
import queue
import struct
import requests

from typing import Union, List
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from pysolarmanv5 import NoSocketAvailableError

from deye_exceptions import (
  DeyeConnectionErrorException,
  DeyeKnownException,
  DeyeNoSocketAvailableException,
  DeyeQueueIsEmptyException,
  DeyeUnknownException,
  DeyeValueException,
)

# some code is based on githubDante / deye-controller
# https://github.com/githubDante/deye-controller

def from_long_register_values(values: List[int], scale: int) -> float:
  value = to_unsigned_bytes(values[::-1])
  return int.from_bytes(value, byteorder = 'big') / scale

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
def to_signed(val: int) -> int:
  return struct.unpack('>h', struct.pack('>H', val))[0]

def to_unsigned(val: int) -> int:
  return struct.unpack('>H', struct.pack('>h', val))[0]

# Convert PDU integer or list with integers to bytes (signed)
# It's needed for a bunch of Deye registers (SN, Time, etc.)
def to_bytes(val: Union[int, List[int]]):
  if isinstance(val, List):
    return bytes.fromhex(''.join([struct.pack('>h', x).hex() for x in val]))
  elif isinstance(val, int):
    return struct.pack('>h', val)
  else:
    raise DeyeValueException(f'to_bytes(): not int / List[int]: {str(val)}')

# Convert PDU integer(s) to byte(s)
# Needed for registers marked with Wh/Wh_high/Wh_low in the Modbus documentation
def to_unsigned_bytes(val: Union[int, List[int]]) -> bytes:
  if isinstance(val, List):
    return bytes.fromhex(''.join([struct.pack('>H', x).hex() for x in val]))
  elif isinstance(val, int):
    return struct.pack('>H', val)
  else:
    raise DeyeValueException(f'to_unsigned_bytes(): not int / List[int]: {str(val)}')

# Convert a sequence of integers (Year, Month, Date, Hour, Minute, Second)
# to 3 bytes tuple suitable for writing though pysolarman
def to_inv_time(vals: List[int]) -> List[int]:
  return list(struct.unpack('>hhh', struct.pack('>bbbbbb', *vals)))

def format_end_date(date: datetime) -> str:
  date_str1 = date.strftime('%Y-%m-%d')
  date_str2 = datetime.now().strftime('%Y-%m-%d')
  date_str3 = (datetime.now() + timedelta(hours = 24)).strftime('%Y-%m-%d')

  return 'today, ' + date.strftime('%H:%M') if date_str1 == date_str2 else\
    ('tomorrow, ' + date.strftime('%H:%M') if date_str1 == date_str3 else\
    date.strftime('%Y-%m-%d, %H:%M'))

def custom_round(num: float) -> str:
  """
  Round a floating-point number to two decimal places using "round half up" rules.

  This function:
    - Converts the input float into a Decimal to avoid floating-point precision errors.
    - Rounds the number to exactly two decimal places.
    - Uses ROUND_HALF_UP, meaning values ending with 5 in the third decimal place 
      are rounded upward (e.g., 1.305 → 1.31).
    - Removes trailing zeros in the fractional part (e.g., 1.50 → "1.5").
    - Returns the result as a string.

  Args:
      num (float): The number to round.

  Returns:
      str: The rounded number as a string.
  """
  # Convert the float to a string, then to Decimal, to avoid binary float issues
  d = Decimal(num)

  # Round to two decimal places with ROUND_HALF_UP strategy
  rounded = d.quantize(Decimal("0.01"), rounding = ROUND_HALF_UP)

  # Format as fixed-point (avoids scientific notation like 2.5E+2)
  s = format(rounded, "f")

  # Strip trailing zeros and possible trailing dot
  return s.rstrip("0").rstrip(".")

def format_timedelta(td: timedelta, add_seconds: bool = False) -> str:
  seconds = int(td.total_seconds())

  if abs(seconds) < 1:
    return '0s'
  elif abs(seconds) < 2:
    return '1s'

  periods = [
    (' year', 60 * 60 * 24 * 365),
    (' month', 60 * 60 * 24 * 30),
    ('d', 60 * 60 * 24),
    ('h', 60 * 60),
    ('m', 60),
    #('s',      1)
  ]

  if add_seconds:
    periods.append(('s', 1))

  strings = []

  for period_name, period_seconds in periods:
    if abs(seconds) > period_seconds:
      period_value, seconds = divmod(abs(seconds), period_seconds)
      strings.append("%s%s" % (period_value, period_name))

  sign = "-" if seconds < 0 else ""
  return sign + " ".join(strings)

# Ensure that the specified directory exists
# If it does not exist, create it (including all intermediate directories)
# and apply the specified permissions (mode)
def ensure_dir_exists(path, mode = 0o755):
  # Create all parent directories if they do not exist
  if not os.path.exists(path):
    os.makedirs(path, exist_ok = True)
    os.chmod(path, mode)

# Ensure that the specified file exists
# If it does not exist, create an empty fil
# and apply the specified permissions (mode)
def ensure_file_exists(path, mode = 0o644):
  # Create the file itself if it does not exist
  if not os.path.exists(path):
    open(path, 'w').close()
    os.chmod(path, mode)

# Ensure that both the parent directory and the file exist
# If the directory does not exist, create it with dir_mode
# If the file does not exist, create it with file_mode
def ensure_dir_and_file_exists(path, dir_mode = 0o755, file_mode = 0o644):
  dir_path = os.path.dirname(path)
  ensure_dir_exists(dir_path, dir_mode)
  ensure_file_exists(path, file_mode)

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
    match = re.search(r"\[Errno -?\d+\][^')]+", str(e))
    text = match.group(0) if match else str(e)
    return DeyeConnectionErrorException(f'{message}: Connection error ({text})')
  except Exception as e:
    return DeyeUnknownException(f'{message}: {str(e)}')
