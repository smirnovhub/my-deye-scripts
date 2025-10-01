from typing import Any, List, Union

from datetime import datetime
from deye_base_enum import DeyeBaseEnum
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_utils import custom_round

class BaseDeyeRegister(DeyeRegister):
  def __init__(self,
               address: int,
               quantity: int,
               name: str,
               description: str,
               suffix: str,
               avg = DeyeRegisterAverageType.none):
    self._address = address
    self._quantity = quantity
    self._scale: int = 1
    self._name = name
    self._description = description
    self._suffix = suffix
    self._avg = avg
    self._value: Union[int, float, str, datetime, DeyeBaseEnum] = 0
    self._min_value: Union[int, float] = 0
    self._max_value: Union[int, float] = 0
    self._loggers = DeyeLoggers()

  def enqueue(self, interactor: DeyeModbusInteractor):
    if interactor.is_master or self._avg != DeyeRegisterAverageType.only_master:
      interactor.enqueue_register(self.address, self.quantity)

  def read(self, interactors: List[DeyeModbusInteractor]):
    if len(interactors) == 1:
      self._value = self.read_from_master_interactor(interactors)
      return self._value

    if self._avg == DeyeRegisterAverageType.accumulate or self._avg == DeyeRegisterAverageType.average:
      value = 0.0
      for interactor in interactors:
        value += self.read_internal(interactor)

      if self._avg == DeyeRegisterAverageType.average:
        value /= len(interactors)

      self._value = value
      return self._value

    self._value = self.read_from_master_interactor(interactors)
    return self._value

  def read_from_master_interactor(self, interactors: List[DeyeModbusInteractor]):
    master_interactor = None
    for interactor in interactors:
      if interactor.name == self._loggers.master.name:
        master_interactor = interactor

    if master_interactor == None:
      master_interactor = interactors[0]

    return self.read_internal(master_interactor)

  @property
  def can_write(self) -> bool:
    return False

  @property
  def can_accumulate(self) -> bool:
    return self._avg != DeyeRegisterAverageType.none and self._avg != DeyeRegisterAverageType.only_master

  @property
  def avg_type(self) -> DeyeRegisterAverageType:
    return self._avg

  @property
  def address(self) -> int:
    return self._address

  @property
  def addresses(self) -> List[int]:
    addr_list = []
    for i in range(self.quantity):
      addr_list.append(self.address + i)
    return addr_list

  @property
  def quantity(self) -> int:
    return self._quantity

  @property
  def name(self) -> str:
    return self._name

  @property
  def description(self) -> str:
    return self._description

  @property
  def value(self) -> Any:
    return self._value

  @property
  def pretty_value(self) -> str:
    if isinstance(self.value, float):
      return custom_round(self.value)
    elif isinstance(self.value, DeyeBaseEnum):
      return self.value.pretty
    elif isinstance(self.value, datetime):
      return self.value.strftime('%Y-%m-%d %H:%M:%S')

    return str(self.value)

  @property
  def suffix(self) -> str:
    return self._suffix

  @property
  def min_value(self) -> float:
    return self._min_value

  @property
  def max_value(self) -> float:
    return self._max_value
