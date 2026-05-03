from typing import List, Optional
from datetime import datetime

from deye_exceptions import DeyeCacheException

class DeyeRegisterCacheData:
  """Container for register data and its caching metadata."""
  def __init__(
    self,
    address: int,
    quantity: int,
    caching_time: int,
    read_ts: float = 0,
    values: Optional[List[int]] = None,
  ):
    self._address = address
    self._quantity = quantity
    self._caching_time = caching_time
    self._read_ts = read_ts
    self._values = values if values else [0] * quantity

    if self._quantity != len(self._values):
      raise DeyeCacheException(f"Quantity mismatch for register {address}: "
                               f"expected {self._quantity}, but got {len(self._values)} values.")

  @property
  def address(self) -> int:
    return self._address

  @property
  def quantity(self) -> int:
    return self._quantity

  @property
  def caching_time(self) -> int:
    return self._caching_time

  @property
  def read_ts(self) -> float:
    return self._read_ts

  @property
  def values(self) -> List[int]:
    return self._values

  def __repr__(self) -> str:
    # Convert timestamp to human-readable format if it exists
    ts_str = datetime.fromtimestamp(self._read_ts).strftime('%Y-%m-%d %H:%M:%S') if self._read_ts > 0 else "N/A"

    # Return formatted string representation of the register data
    return (f"Register(address: {self._address}, "
            f"quantity: {self._quantity}, "
            f"values: {self._values}, "
            f"caching_time: {self._caching_time}s, "
            f"read_at: {ts_str})")
