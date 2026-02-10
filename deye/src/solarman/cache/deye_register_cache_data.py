from typing import List, Optional

class DeyeRegisterCacheData:
  """Container for register data and its caching metadata."""
  def __init__(
    self,
    address: int,
    quantity: int,
    cache_time: int,
    values: Optional[List[int]] = None,
  ):
    self._address = address
    self._quantity = quantity
    self._cache_time = cache_time
    self._values = values if values else [0] * quantity

    if self._quantity != len(self._values):
      raise ValueError(f"Quantity mismatch for register {address}: "
                       f"expected {self._quantity}, but got {len(self._values)} values.")

  @property
  def address(self) -> int:
    return self._address

  @property
  def quantity(self) -> int:
    return self._quantity

  @property
  def cache_time(self) -> int:
    return self._cache_time

  @property
  def values(self) -> List[int]:
    return self._values
