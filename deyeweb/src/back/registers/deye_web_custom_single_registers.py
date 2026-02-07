from typing import List

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class DeyeWebCustomSingleRegisters(DeyeRegisters):
  def __init__(self, register: DeyeRegister, prefix: str = ''):
    super().__init__(prefix)
    self._registers: List[DeyeRegister] = [register]

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return self._registers
