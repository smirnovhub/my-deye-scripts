from typing import List

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class CustomRegisters(DeyeRegisters):
  def __init__(self, register_names: List[str], prefix: str = ''):
    super().__init__(prefix)

    self._registers: List[DeyeRegister] = []
    for register_name in register_names:
      reg = self.get_register_by_name(register_name)
      if reg is not None:
        self._registers.append(reg)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return self._registers
