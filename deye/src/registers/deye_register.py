from typing import List

from deye_modbus_interactor import DeyeModbusInteractor
from deye_exceptions import DeyeNotImplementedException
from deye_exceptions import DeyeValueException

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
  def can_write(self):
    self.not_implemented('can_write')

  @property
  def can_accumulate(self):
    self.not_implemented('can_accumulate')

  @property
  def type_name(self):
    self.not_implemented('type_name')

  @property
  def address(self):
    self.not_implemented('address')

  @property
  def addresses(self):
    self.not_implemented('address')

  @property
  def quantity(self):
    self.not_implemented('quantity')

  @property
  def name(self):
    self.not_implemented('name')

  @property
  def description(self):
    self.not_implemented('description')

  @property
  def value(self):
    self.not_implemented('value')

  @property
  def suffix(self):
    self.not_implemented('suffix')

  @property
  def min_value(self):
    self.not_implemented('min_value')

  @property
  def max_value(self):
    self.not_implemented('max_value')

  def error(self, message):
    raise DeyeValueException(f'{type(self).__name__}.{message}')

  def not_implemented(self, message):
    raise DeyeNotImplementedException(f'{type(self).__name__}.{message} is not implemented')
