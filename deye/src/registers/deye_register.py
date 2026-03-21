from typing import Any, List, Optional

from datetime import timedelta
from abc import ABC, abstractmethod

from deye_exceptions import DeyeNotImplementedException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class DeyeRegister(ABC):
  @abstractmethod
  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    pass

  @abstractmethod
  def read(self, interactors: List[DeyeModbusInteractor]) -> Any:
    pass

  @abstractmethod
  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    pass

  def write(self, interactor: DeyeModbusInteractor, value: Any) -> Any:
    DeyeNotImplementedException(f'{type(self).__name__} write() is not implemented')

  @property
  def can_write(self) -> bool:
    return False

  @property
  def can_accumulate(self) -> bool:
    return self.avg_type != DeyeRegisterAverageType.none and self.avg_type != DeyeRegisterAverageType.only_master

  @property
  @abstractmethod
  def avg_type(self) -> DeyeRegisterAverageType:
    pass

  @property
  @abstractmethod
  def address(self) -> int:
    pass

  @property
  @abstractmethod
  def addresses(self) -> List[int]:
    pass

  @property
  @abstractmethod
  def quantity(self) -> int:
    pass

  @property
  @abstractmethod
  def name(self) -> str:
    pass

  @property
  @abstractmethod
  def description(self) -> str:
    pass

  @property
  @abstractmethod
  def value(self) -> Any:
    pass

  @property
  @abstractmethod
  def pretty_value(self) -> str:
    pass

  @property
  @abstractmethod
  def suffix(self) -> str:
    pass

  @property
  @abstractmethod
  def min_value(self) -> float:
    pass

  @property
  @abstractmethod
  def max_value(self) -> float:
    pass

  @property
  def caching_time(self) -> Optional[timedelta]:
    return None
