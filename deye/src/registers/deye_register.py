from typing import Any, List

from deye_modbus_interactor import DeyeModbusInteractor
from deye_exceptions import DeyeNotImplementedException
from deye_exceptions import DeyeValueException
from deye_register_average_type import DeyeRegisterAverageType

class DeyeRegister:
  def enqueue(self, interactor: DeyeModbusInteractor):
    raise self.not_implemented('enqueue()')

  def read(self, interactors: List[DeyeModbusInteractor]):
    raise self.not_implemented('read()')

  def write(self, interactor: DeyeModbusInteractor, value):
    raise self.not_implemented('write()')

  def read_internal(self, interactor: DeyeModbusInteractor):
    raise self.not_implemented('read_internal()')

  @property
  def can_write(self) -> bool:
    raise self.not_implemented('can_write')

  @property
  def can_accumulate(self) -> bool:
    raise self.not_implemented('can_accumulate')

  @property
  def avg_type(self) -> DeyeRegisterAverageType:
    raise self.not_implemented('avg_type')

  @property
  def address(self) -> int:
    raise self.not_implemented('address')

  @property
  def addresses(self) -> List[int]:
    raise self.not_implemented('addresses')

  @property
  def quantity(self) -> int:
    raise self.not_implemented('quantity')

  @property
  def name(self) -> str:
    raise self.not_implemented('name')

  @property
  def description(self) -> str:
    raise self.not_implemented('description')

  @property
  def value(self) -> Any:
    raise self.not_implemented('value')

  @property
  def suffix(self) -> str:
    raise self.not_implemented('suffix')

  @property
  def min_value(self) -> float:
    raise self.not_implemented('min_value')

  @property
  def max_value(self) -> float:
    raise self.not_implemented('max_value')

  def error(self, message: str):
    raise DeyeValueException(f'{type(self).__name__}.{message}')

  def not_implemented(self, message: str):
    return DeyeNotImplementedException(f'{type(self).__name__}.{message} is not implemented')
