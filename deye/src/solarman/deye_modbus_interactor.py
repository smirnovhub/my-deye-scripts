from abc import ABC, abstractmethod

from typing import List, Optional
from datetime import timedelta

class DeyeModbusInteractor(ABC):
  @property
  @abstractmethod
  def name(self) -> str:
    pass

  @property
  @abstractmethod
  def is_master(self) -> bool:
    pass

  @abstractmethod
  def enqueue_register(
    self,
    address: int,
    quantity: int,
    caching_time: Optional[timedelta],
  ) -> None:
    pass

  @abstractmethod
  def read_register(self, address: int, quantity: int) -> List[int]:
    pass

  @abstractmethod
  def write_register(self, address: int, values: List[int]) -> int:
    pass
