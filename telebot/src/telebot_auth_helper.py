from typing import List
from telebot_user import TelebotUser
from telebot_users import TelebotUsers
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_menu_item import TelebotMenuItem

class TelebotAuthHelper:
  def get_allowed_menu_items(self, user: TelebotUser, items: List[TelebotMenuItemHandler]) -> List[TelebotMenuItemHandler]:
    allowed_items = []

    for item in items:
      if item.command in user.allowed_menu_items:
        allowed_items.append(item)

    return allowed_items

  def is_menu_item_allowed(self, users: TelebotUsers, user_id: str, item: TelebotMenuItem) -> bool:
    user = users.get_user(user_id)
    return item in user.allowed_menu_items if user else False

  def is_writable_register_allowed(self, users: TelebotUsers, user_id: str, command: str) -> bool:
    user = users.get_user(user_id)
    command = command.lstrip('/')
    if command in user.disabled_writable_registers:
      return False

    if user.allowed_writable_registers:
      if command in user.allowed_writable_registers:
        return True
      return False

    return True
