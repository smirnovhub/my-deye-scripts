from typing import Union
from telebot_user import TelebotUser
from telebot_users import TelebotUsers
from telebot_menu_item import TelebotMenuItem

class TelebotAuthHelper:
  """
  A helper class for handling user permissions and access control
  for menu items and writable registers in a Telebot-based system.
  """
  def __init__(self):
    self.users = TelebotUsers()

  def is_menu_item_allowed(self, user_id: int, item: TelebotMenuItem) -> bool:
    """
    Check if a menu item is allowed for a given user ID.

    Args:
        user_id (int): Telegram user ID.
        item (TelebotMenuItem): The menu item to check.

    Returns:
        bool: True if the menu item is allowed, False otherwise.
    """
    if self.users.is_user_blocked(user_id):
      return False
    user = self.users.get_allowed_user(user_id)
    return self.is_menu_item_allowed_for_user(user, item)

  def is_menu_item_allowed_for_user(self, user: Union[TelebotUser, None], item: TelebotMenuItem) -> bool:
    """
    Check if a menu item is allowed for a specific TelebotUser instance.

    Args:
        user (TelebotUser | None): The user object, or None if not found.
        item (TelebotMenuItem): The menu item to check.

    Returns:
        bool: True if the menu item is allowed, False otherwise.
    """
    if user is None:
      return False

    if self.users.is_user_blocked(user.id):
      return False

    if item in user.disabled_menu_items:
      return False

    if user.allowed_menu_items:
      return item in user.allowed_menu_items

    return True

  def is_writable_register_allowed(self, user_id: int, register_name: str) -> bool:
    """
    Check if a user is allowed to write to a specific register.

    The method considers blocked users, disabled writable registers,
    and optionally a whitelist of allowed writable registers.

    Args:
        user_id (int): Telegram user ID.
        register_name (str): Name of the register (leading '/' will be stripped).

    Returns:
        bool: True if the user is allowed to write to the register, False otherwise.
    """
    if self.users.is_user_blocked(user_id):
      return False

    user = self.users.get_allowed_user(user_id)
    register_name = register_name.lstrip('/')

    for register in user.disabled_writable_registers:
      if register_name == register.name:
        return False

    if user.allowed_writable_registers:
      for register in user.allowed_writable_registers:
        if register_name == register.name:
          return True
      return False

    return True
