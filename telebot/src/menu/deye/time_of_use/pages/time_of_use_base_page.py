from typing import Any, Sequence

from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseBasePage(TelebotNavigationPage):
  def __init__(self):
    super().__init__()

  def check_bounds(self, collection: Sequence[Any], index: int) -> None:
    count = len(collection)
    if not (0 <= index < count):
      class_name = self.__class__.__name__
      raise RuntimeError(f"{class_name}: index {index} is out of bounds (0 to {count - 1})")
