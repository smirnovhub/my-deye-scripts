import math

from typing import Any, List, Optional, Union
from datetime import datetime, timedelta

from deye_utils import DeyeUtils
from deye_base_enum import DeyeBaseEnum
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_exceptions import DeyeValueException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class BaseDeyeRegister(DeyeRegister):
  def __init__(
    self,
    address: int,
    quantity: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
    avg = DeyeRegisterAverageType.none,
    caching_time: Optional[timedelta] = None,
  ):
    self._address = address
    self._quantity = quantity
    self._scale: int = 1
    self._name = description.replace(" ", "_").replace("-", "_").lower()
    self._description = description
    self._suffix = suffix
    self._group = group
    self._avg = avg
    self._value: Union[int, float, str, datetime, DeyeBaseEnum, List[int]] = 0
    self._min_value: Union[int, float] = 0
    self._max_value: Union[int, float] = 0
    self._caching_time = caching_time
    self._loggers = DeyeLoggers()
    self._writable_registers_caching_time = timedelta(hours = 12)

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    if self.can_read(interactor):
      interactor.enqueue_register(self.address, self.quantity, self.caching_time)

  def read(self, interactors: List[DeyeModbusInteractor]) -> None:
    if len(interactors) == 1:
      self._value = self.read_internal(interactors[0])
      return

    if self._avg == DeyeRegisterAverageType.fake_accumulate:
      value = self.read_from_master_interactor(interactors)

      # Check if the value is a number before multiplication
      if isinstance(value, (int, float)):
        value *= len(interactors)
      else:
        # Handle the error if the type is unexpected
        class_name = self.__class__.__name__
        raise DeyeValueException(f"{class_name}: you can use {self._avg.name} only for "
                                 f"numeric registers, but got {type(value).__name__}")

      self._value = value
    elif self._avg == DeyeRegisterAverageType.accumulate:
      total: Union[int, float]

      if isinstance(self._value, int):
        total = 0
      else:
        total = 0.0

      for interactor in interactors:
        total += self.read_internal(interactor)
      self._value = total
    elif self._avg == DeyeRegisterAverageType.average:
      total = 0.0
      divider = len(interactors)

      from int_deye_register import IntDeyeRegister
      from float_deye_register import FloatDeyeRegister

      digits = round(math.log10(self.scale)) if isinstance(self, FloatDeyeRegister) else 2

      for interactor in interactors:
        total += round(self.read_internal(interactor) / divider, digits)

      self._value = round(total, digits)

      if isinstance(self, IntDeyeRegister):
        self._value = round(self._value)
    else:
      self._value = self.read_from_master_interactor(interactors)

  def read_from_master_interactor(self, interactors: List[DeyeModbusInteractor]) -> Any:
    master_interactor = None
    for interactor in interactors:
      if interactor.name == self._loggers.master.name:
        master_interactor = interactor

    if master_interactor == None:
      raise RuntimeError(f"Master interactor not found for register {self.address} {self.name}")

    return self.read_internal(master_interactor)

  @property
  def group(self) -> DeyeRegisterGroup:
    return self._group

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
      return DeyeUtils.custom_round(self.value)
    elif isinstance(self.value, DeyeBaseEnum):
      return self.value.pretty
    elif isinstance(self.value, datetime):
      return self.value.strftime(DeyeUtils.time_format_str)

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

  @property
  def caching_time(self) -> Optional[timedelta]:
    if self.can_write and self._loggers.remote_cache_server:
      return self._writable_registers_caching_time
    return self._caching_time

  def error(self, message: str):
    raise DeyeValueException(f'{type(self).__name__}.{message}')
