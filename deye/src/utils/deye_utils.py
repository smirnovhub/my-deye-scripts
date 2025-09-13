import os
import struct

from typing import Union, List
from datetime import datetime, timedelta
from deye_exceptions import DeyeValueException

# some code is based on githubDante / deye-controller
# https://github.com/githubDante/deye-controller

def get_long_register_value(values: List[int], divider: int) -> float:
  value = to_unsigned_bytes(values[::-1])
  return int.from_bytes(value, byteorder='big') / divider

# Convert PDU integer or list with integers to bytes (signed)
# It's needed for a bunch of Deye registers (SN, Time, etc.)
def to_signed(val: int) -> int:
  return struct.unpack('>h', struct.pack('>H', val))[0]

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

def format_end_date(date:datetime) -> str:
  date_str1 = date.strftime('%Y-%m-%d')
  date_str2 = datetime.now().strftime('%Y-%m-%d')
  date_str3 = (datetime.now() + timedelta(hours = 24)).strftime('%Y-%m-%d')

  return 'today, ' + date.strftime('%H:%M') if date_str1 == date_str2 else\
    ('tomorrow, ' + date.strftime('%H:%M') if date_str1 == date_str3 else\
    date.strftime('%Y-%m-%d, %H:%M'))

def have_second_sign(num: float):
  if type(num) is not float:
    return False

  num = round(num, 3)
  num = num % 1
  num = round(num * 1000)
  num -= num % 10
  num /= 10

  return num % 10 > 0

def format_timedelta(td:timedelta, add_seconds:bool = False) -> str:
  seconds = int(td.total_seconds())

  if abs(seconds) < 1:
    return '0s'
  elif abs(seconds) < 2:
    return '1s'

  periods = [
    (' year',  60 * 60 * 24 * 365),
    (' month', 60 * 60 * 24 * 30),
    ('d',      60 * 60 * 24),
    ('h',      60 * 60),
    ('m',      60),
    #('s',      1)
  ]

  if add_seconds:
    periods.append(('s', 1))

  strings = []

  for period_name, period_seconds in periods:
    if abs(seconds) > period_seconds:
      period_value , seconds = divmod(abs(seconds), period_seconds)
      strings.append("%s%s" % (period_value, period_name))

  sign = "-" if seconds < 0 else ""
  return sign + " ".join(strings)

# Ensure that the specified directory exists
# If it does not exist, create it (including all intermediate directories)
# and apply the specified permissions (mode)
def ensure_dir_exists(path, mode=0o755):
  # Create all parent directories if they do not exist
  if not os.path.exists(path):
    os.makedirs(path, exist_ok=True)
    os.chmod(path, mode)

# Ensure that the specified file exists
# If it does not exist, create an empty fil
# and apply the specified permissions (mode)
def ensure_file_exists(path, mode=0o644):
  # Create the file itself if it does not exist
  if not os.path.exists(path):
    open(path, 'w').close()
    os.chmod(path, mode)

# Ensure that both the parent directory and the file exist
# If the directory does not exist, create it with dir_mode
# If the file does not exist, create it with file_mode
def ensure_dir_and_file_exists(path, dir_mode=0o755, file_mode=0o644):
  dir_path = os.path.dirname(path)
  ensure_dir_exists(dir_path, dir_mode)
  ensure_file_exists(path, file_mode)
