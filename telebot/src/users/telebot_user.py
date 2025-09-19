from typing import List

from deye_register import DeyeRegister
from telebot_menu_item import TelebotMenuItem

class TelebotUser:
  """
  Represents a Telebot user with permissions for menu items and writable registers
  """
  def __init__(
    self,
    name: str,
    id: int,
    allowed_menu_items: List[TelebotMenuItem] = [],
    disabled_menu_items: List[TelebotMenuItem] = [],
    allowed_writable_registers: List[DeyeRegister] = [],
    disabled_writable_registers: List[DeyeRegister] = [],
  ):
    """
    Initialize a TelebotUser instance

    Args:
        name (str): User's display name
        id (int): Telegram user ID
        allowed_menu_items (List[TelebotMenuItem], optional): Menu items explicitly allowed for this user. Default is empty (all allowed)
        disabled_menu_items (List[TelebotMenuItem], optional): Menu items explicitly disabled for this user. Default is empty (none disabled)
        allowed_writable_registers (List[DeyeRegister], optional): Writable registers explicitly allowed for this user. Default is empty (all allowed)
        disabled_writable_registers (List[DeyeRegister], optional): Writable registers explicitly disabled for this user. Default is empty (none disabled)
    """
    self._name = name
    self._id = id
    # Empty - means all allowed
    self._allowed_menu_items = allowed_menu_items
    # Empty - means none disabled (all allowed)
    self._disabled_menu_items = disabled_menu_items
    # Empty - means all allowed
    self._allowed_writable_registers = allowed_writable_registers
    # Empty - means none disabled (all allowed)
    self._disabled_writable_registers = disabled_writable_registers

  @property
  def name(self) -> str:
    """Get the user's display name"""
    return self._name

  @property
  def id(self) -> int:
    """Get the user's Telegram ID"""
    return self._id

  @property
  def allowed_menu_items(self) -> List[TelebotMenuItem]:
    """Get the list of explicitly allowed menu items. Empty list means all are allowed"""
    return self._allowed_menu_items

  @property
  def disabled_menu_items(self) -> List[TelebotMenuItem]:
    """Get the list of disabled menu items. Empty list means none are disabled"""
    return self._disabled_menu_items

  @property
  def allowed_writable_registers(self) -> List[DeyeRegister]:
    """Get the list of explicitly allowed writable registers. Returns a copy to prevent external modification"""
    return self._allowed_writable_registers.copy()

  @property
  def disabled_writable_registers(self) -> List[DeyeRegister]:
    """Get the list of disabled writable registers. Returns a copy to prevent external modification"""
    return self._disabled_writable_registers.copy()
