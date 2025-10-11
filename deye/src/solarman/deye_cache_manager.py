import os
import re
import json
import time

from datetime import datetime

from deye_utils import DeyeUtils
from deye_file_lock import DeyeFileLock

# -------------------------------
# Class for caching register data
# -------------------------------
class DeyeCacheManager:
  def __init__(self, name: str, cache_path: str, caching_time: int, verbose = False):
    self.name = name
    self.cache_path = cache_path
    self.caching_time = caching_time
    self.verbose = verbose

  def get_cache_filename(self, register_addr, quantity) -> str:
    return os.path.join(self.cache_path, f"registers-{self.name}-{register_addr}-{quantity}.json")

  def save_to_cache(self, register_addr, quantity, data):
    filename = self.get_cache_filename(register_addr, quantity)
    now = datetime.now().strftime(DeyeUtils.time_format_str)

    DeyeUtils.ensure_file_exists(filename, mode = 0o666)

    if self.verbose:
      print(f"{self.name}: saving cache to {filename}...")

    with open(filename, "r+", encoding = "utf-8") as f:
      try:
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_EX)
        f.seek(0)
        f.truncate(0)
        json.dump(
          {
            "name": self.name,
            "time": now,
            "address": register_addr,
            "quantity": quantity,
            "data": data
          },
          f,
          ensure_ascii = False,
          indent = 2,
        )
      finally:
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

    if self.verbose:
      print(f"{self.name}: saved to cache address = {register_addr}, quantity = {quantity}, data = {data}")

  def load_from_cache(self, register_addr, quantity):
    if self.caching_time < 1:
      return None

    filename = self.get_cache_filename(register_addr, quantity)
    if not os.path.exists(filename):
      if self.verbose:
        print(f"{self.name}: cached data for address = {register_addr}, quantity = {quantity} not found")
      return None

    # Check if cache is still valid
    mtime = os.path.getmtime(filename)
    now = time.time()
    if now - mtime > self.caching_time:
      if self.verbose:
        print(f"{self.name}: cache for address = {register_addr}, quantity = {quantity} has expired")
      return None

    if self.verbose:
      print(
        f"{self.name}: cache for address = {register_addr}, quantity = {quantity} will expire in {int(round(self.caching_time - now + mtime))} sec"
      )

    with open(filename, "r", encoding = "utf-8") as f:
      try:
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_SH)
        content = json.load(f)
      finally:
        DeyeFileLock.flock(f, DeyeFileLock.LOCK_UN)

    return content.get("data")

  def remove_overlapping(self, register_addr, values):
    # Remove cache files overlapping with the given register range
    to_delete_start = register_addr
    to_delete_end = register_addr + len(values) - 1 # inclusive

    pattern = re.compile(rf"registers-.+-(\d+)-(\d+)\.json")

    if self.verbose:
      print(f'{self.name}: removing cached files for registers {[register_addr + i for i in range(len(values))]}...')

    # Iterate over all files in the cache directory
    for fname in os.listdir(self.cache_path):
      match = pattern.fullmatch(fname)
      if match:
        # Extract start address and length from filename
        from_file_start = int(match.group(1))
        length = int(match.group(2))
        from_file_end = from_file_start + length - 1 # inclusive

        # Check if the write range overlaps with file range
        if not (to_delete_end < from_file_start or to_delete_start > from_file_end):
          if self.verbose:
            print(f'{self.name}: remove {fname}')

          # Attempt to delete the file
          os.remove(os.path.join(self.cache_path, fname))
