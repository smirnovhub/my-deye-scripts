from typing import List, Union
from deye_register import DeyeRegister
from deye_registers_factory import DeyeRegistersFactory

class EmptyRegisters(DeyeRegistersFactory.get_registers_class()):
  def __init__(self, prefix: str = ''):
    super().__init__(prefix)

  @property
  def all_registers(self) -> List[DeyeRegister]:
    return []
