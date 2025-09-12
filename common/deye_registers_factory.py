from typing import Type
from deye_registers import DeyeRegisters
from deye_sun6k_sg03lp1_registers import DeyeSun6kSg03Lp1Registers

class DeyeRegistersFactory:
  @staticmethod
  def get_registers_class() -> Type[DeyeRegisters]:
    return DeyeSun6kSg03Lp1Registers
  
  @staticmethod
  def create_registers(prefix: str = '') -> DeyeRegisters:
    return DeyeRegistersFactory.get_registers_class()(prefix)
