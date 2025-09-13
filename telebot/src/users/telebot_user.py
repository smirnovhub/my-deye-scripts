from typing import List
from telebot_menu_command import TelebotMenuCommand
from telebot_menu_item import TelebotMenuItem

class TelebotUser:
  def __init__(self, name: str, id: str, allowed_commands: List[TelebotMenuCommand]):
    self._name = name
    self._id = id
    self._allowed_commands = allowed_commands

  @property
  def name(self) -> str:
    return self._name

  @property
  def id(self) -> str:
    return self._id

  @property
  def allowed_commands(self) -> List[TelebotMenuCommand]:
    return self._allowed_commands

  def get_allowed_menu_items(self, commands: List[TelebotMenuItem]) -> List[TelebotMenuItem]:
    allowed_items = []

    for command in commands:
      if command.command in self._allowed_commands:
        allowed_items.append(command)

    return allowed_items
  