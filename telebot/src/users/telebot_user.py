from typing import List
from telebot_menu_item import TelebotMenuItem

class TelebotUser:
  def __init__(self, name: str, id: str,
               allowed_menu_items: List[TelebotMenuItem],
               allowed_writable_registers: List[str] = [],
               disabled_writable_registers: List[str] = []):
    self._name = name
    self._id = id
    # empty - means none allowed
    self._allowed_menu_items = allowed_menu_items
    # empty - means all allowed
    self._allowed_writable_registers = allowed_writable_registers
    # empty - means none disabled (all allowed)
    self._disabled_writable_registers = disabled_writable_registers

  @property
  def name(self) -> str:
    return self._name

  @property
  def id(self) -> str:
    return self._id

  @property
  def allowed_menu_items(self) -> List[TelebotMenuItem]:
    return self._allowed_menu_items
  
  @property
  def allowed_writable_registers(self) -> List[str]:
    return [register.replace('master_', '') for register in self._allowed_writable_registers]
  
  @property
  def disabled_writable_registers(self) -> List[str]:
    return [register.replace('master_', '') for register in self._disabled_writable_registers]
