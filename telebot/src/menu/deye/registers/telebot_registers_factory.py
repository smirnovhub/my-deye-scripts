from typing import Optional, Type, TypeVar, Dict, Callable, Any

from simple_singleton import singleton
from accumulated_info_registers import AccumulatedInfoRegisters
from all_settings_registers import AllSettingsRegisters
from charge_current_registers1 import ChargeCurrentRegisters1
from charge_current_registers2 import ChargeCurrentRegisters2
from forecast_registers import ForecastRegisters
from master_info_registers import MasterInfoRegisters
from master_settings_registers import MasterSettingsRegisters
from slave_info_registers import SlaveInfoRegisters
from today_stat_registers import TodayStatRegisters
from total_stat_registers import TotalStatRegisters

T = TypeVar("T")

@singleton
class TelebotRegistersFactory:
  """
  Type-to-constructor factory.

  Key = exact type.
  Value = callable that creates it.
  """
  def __init__(self) -> None:
    self._registry: Dict[Type[Any], Callable[..., Any]] = {}

    registers = [
      AccumulatedInfoRegisters,
      AllSettingsRegisters,
      ChargeCurrentRegisters1,
      ChargeCurrentRegisters2,
      ForecastRegisters,
      MasterInfoRegisters,
      MasterSettingsRegisters,
      SlaveInfoRegisters,
      TodayStatRegisters,
      TotalStatRegisters,
    ]

    for cls in registers:
      self._register(cls)

  def _register(
    self,
    cls: Type[T],
    constructor: Optional[Callable[..., T]] = None,
  ) -> None:
    """
    Register a type.

    :param cls: Type to register
    :param constructor: Optional custom constructor (defaults to cls)
    """
    if cls in self._registry:
      raise KeyError(f"{cls} already registered")

    self._registry[cls] = constructor or cls

  def create(
    self,
    cls: Type[T],
    *args,
    **kwargs,
  ) -> T:
    """
    Create instance by exact type.
    """
    if cls not in self._registry:
      raise KeyError(f"{cls} is not registered")

    return self._registry[cls](*args, **kwargs)
