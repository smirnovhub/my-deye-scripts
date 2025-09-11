from typing import List
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters

class SingleRegister(DeyeRegisters):
  def __init__(self, register, prefix: str = ''):
    super().__init__(prefix)
    self._register = register

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [self._register] if self._register is not None else []
