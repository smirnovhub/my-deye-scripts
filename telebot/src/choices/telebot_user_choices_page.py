from enum import Enum, auto
from typing import Callable, List

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator

class UserChoicePageType(Enum):
  main = auto()

class UserChoicePage(TelebotNavigationPage):
  def __init__(
    self,
    text: str,
    options: List[ButtonNode],
    chat_id: int,
    callback: Callable[[int, ButtonNode], None],
    max_per_row: int = 5,
    accept_wrong_choice_from_user_input: bool = False,
    wrong_choice_text: str = 'No such option',
  ):
    super().__init__()
    self._text = text
    self._options = options
    self._chat_id = chat_id
    self._callback = callback
    self._max_per_row = max_per_row
    self._accept_wrong_choice_from_user_input = accept_wrong_choice_from_user_input
    self._wrong_choice_text = wrong_choice_text
    self._buttons: List[ButtonNode] = []

  @property
  def page_type(self) -> Enum:
    return UserChoicePageType.main

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  @property
  def resend_message_on_user_input(self) -> bool:
    return False

  def update(self) -> None:
    self._buttons = []

    # Iterate with index to manage rows
    for i, button in enumerate(self._options):
      self.register_button_handler(button, self._handle_selection)
      self._buttons.append(button)

      # Add a break if we reached the max items per row OR if it's the last item
      if (i + 1) % self._max_per_row == 0 or (i + 1) == len(self._options):
        self._buttons.append(BreakButtonNode())

  def _handle_selection(self, navigator: TelebotPageNavigator, button: ButtonNode):
    navigator.stop()
    self._callback(self._chat_id, button)

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    try:
      text_lower = text.lower()
      for button in self.buttons:
        if button.text.lower() == text_lower:
          self._callback(self._chat_id, button)
          return

      if self._accept_wrong_choice_from_user_input:
        self._callback(self._chat_id, ButtonNode(text = text))
      else:
        navigator.send_message(self._wrong_choice_text)
    finally:
      navigator.stop()
