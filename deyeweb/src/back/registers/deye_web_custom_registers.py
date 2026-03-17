from typing import List
from functools import cached_property

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class DeyeWebCustomRegisters(DeyeRegisters):
  def __init__(
    self,
    register_names: List[str],
    prefix: str = '',
  ):
    super().__init__(prefix)
    self._register_names = register_names

  @cached_property
  def all_registers(self) -> List[DeyeRegister]:
    registers: List[DeyeRegister] = []
    registers_map = {reg.name: reg for reg in super().all_registers}

    for register_name in self._register_names:
      reg = registers_map.get(register_name)
      if reg is not None:
        registers.append(reg)

    return registers
