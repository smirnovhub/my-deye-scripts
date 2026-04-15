import logging

from typing import Dict, List

from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters

class DeyeRegistersHolder:
  def __init__(
    self,
    loggers: List[DeyeLogger],
    **kwargs,
  ):
    self._registers: Dict[str, DeyeRegisters] = {}
    self._loggers = loggers
    self._log = logging.getLogger()
    self._all_loggers = DeyeLoggers()
    self._socket_timeout = kwargs.get("socket_timeout", 10)

  @property
  def all_registers(self) -> Dict[str, DeyeRegisters]:
    return self._registers

  @property
  def master_registers(self) -> DeyeRegisters:
    return self._registers[self._all_loggers.master.name]

  @property
  def accumulated_registers(self) -> DeyeRegisters:
    return self._registers[self._all_loggers.accumulated_registers_prefix]
