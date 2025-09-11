from typing import List

from deye_modbus_interactor import DeyeModbusInteractor
from deye_exceptions import DeyeNotImplementedException
from deye_exceptions import DeyeValueException
from deye_register_average_type import DeyeRegisterAverageType

class DeyeRegister:
  def enqueue(self, interactor: DeyeModbusInteractor):
    self.not_implemented('enqueue()')

  def read(self, interactors: List[DeyeModbusInteractor]):
    self.not_implemented('read()')

  def write(self, interactor: DeyeModbusInteractor, value):
    self.not_implemented('write()')

  def read_internal(self, interactor: DeyeModbusInteractor):
    self.not_implemented('read_internal()')

  @property
  def can_write(self) -> bool:
    self.not_implemented('can_write')

  @property
  def can_accumulate(self) -> bool:
    self.not_implemented('can_accumulate')

  @property
  def type_name(self) -> str:
    self.not_implemented('type_name')

  @property
  def avg_type(self) -> DeyeRegisterAverageType:
    self.not_implemented('avg_type')

  @property
  def address(self) -> int:
    self.not_implemented('address')

  @property
  def addresses(self) -> List[int]:
    self.not_implemented('address')

  @property
  def quantity(self) -> int:
    self.not_implemented('quantity')

  @property
  def name(self) -> str:
    self.not_implemented('name')

  @property
  def description(self) -> str:
    self.not_implemented('description')

  @property
  def value(self):
    self.not_implemented('value')

  @property
  def suffix(self) -> str:
    self.not_implemented('suffix')

  @property
  def min_value(self) -> float:
    self.not_implemented('min_value')

  @property
  def max_value(self) -> float:
    self.not_implemented('max_value')

  def error(self, message: str):
    raise DeyeValueException(f'{type(self).__name__}.{message}')

  def not_implemented(self, message: str):
    raise DeyeNotImplementedException(f'{type(self).__name__}.{message} is not implemented')
