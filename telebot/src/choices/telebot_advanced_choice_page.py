from enum import Enum, auto
from typing import Callable, List, Optional

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator

class AdvancedChoicePageType(Enum):
  main = auto()

class AdvancedChoicePage(TelebotNavigationPage):
  def __init__(
    self,
    text: str,
    options: List[ButtonNode],
    chat_id: int,
    callback: Optional[Callable[[int, ButtonNode], None]] = None,
    max_per_row: int = 5,
    max_lines_per_page: int = 5,
    edit_message_with_user_selection: bool = False,
  ):
    super().__init__()
    self._text = text
    self._options = options
    self._chat_id = chat_id
    self._callback = callback
    self._max_per_row = max_per_row
    self._max_lines_per_page = max_lines_per_page
    self._edit_message_with_user_selection = edit_message_with_user_selection
    self._current_page_index = 0
    self._buttons: List[ButtonNode] = []
    self._total_pages = (len(self._options) + self._max_lines_per_page - 1) // self._max_lines_per_page

  @property
  def page_type(self) -> Enum:
    return AdvancedChoicePageType.main

  @property
  def need_user_input(self) -> bool:
    return False

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    """
    Logic for building the current page of options.
    """
    start = self._current_page_index * self._max_lines_per_page
    end = start + self._max_lines_per_page
    page_items = self._options[start:end]

    # Add option buttons
    for button in page_items:
      self.register_button_handler(button, self._handle_selection)

    if self._total_pages > 1:
      while len(page_items) < self._max_lines_per_page:
        page_items.append(ButtonNode(" "))

    buttons: List[ButtonNode] = []

    for button in page_items:
      buttons.append(button)
      buttons.append(BreakButtonNode())

    # Add navigation row if needed
    if self._total_pages > 1:
      buttons.append(self.register_button_handler(ButtonNode("Prev"), self._move_prev))

      buttons.append(
        self.register_button_handler(
          ButtonNode(f"{self._current_page_index + 1}/{self._total_pages}"),
          self._move_next,
        ))

      buttons.append(self.register_button_handler(ButtonNode("Next"), self._move_next))

    self._buttons = buttons

  def _move_next(self, navigator: TelebotPageNavigator) -> None:
    self._current_page_index = (self._current_page_index + 1) % self._total_pages
    navigator.update()

  def _move_prev(self, navigator: TelebotPageNavigator) -> None:
    self._current_page_index = (self._current_page_index - 1) % self._total_pages
    navigator.update()

  def _handle_selection(self, navigator: TelebotPageNavigator, button: ButtonNode):
    if self._callback:
      self._callback(self._chat_id, button)

    # Stop navigation and update message
    final_text = f"{self._text} {button.text}" if self._edit_message_with_user_selection else self._text
    navigator.stop(final_text)

  def get_goodbye_message(self) -> str:
    return f"{self._text} cancel"
