from abc import ABC, abstractmethod

class DeyeBaseLocker(ABC):
  @abstractmethod
  def acquire(self, timeout: int = 15) -> None:
    pass

  @abstractmethod
  def release(self) -> None:
    pass
