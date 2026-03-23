from abc import ABC, abstractmethod

class TelebotBaseHandler(ABC):
  @abstractmethod
  def register_handlers(self) -> None:
    pass
