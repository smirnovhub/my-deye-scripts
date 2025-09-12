from typing import List
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory

class SingleRegister(DeyeRegistersFactory.get_registers_class()):
  def __init__(self, register: DeyeRegister, prefix: str = ''):
    super().__init__(prefix)
    self._register = register

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return [self._register] if self._register is not None else []
