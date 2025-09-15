from typing import List
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory

class CustomRegisters(DeyeRegistersFactory.get_registers_class()):
  def __init__(self, registers: List[DeyeRegister], prefix: str = ''):
    super().__init__(prefix)
    self._registers = registers

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return self._registers
