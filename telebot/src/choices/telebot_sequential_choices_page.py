from enum import Enum, auto
from typing import Callable, List

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_sequential_choice_button import SequentialChoiceButton

class SequentialChoicePageType(Enum):
  main = auto()

class SequentialChoicePage(TelebotNavigationPage):
  def __init__(
    self,
    text: str,
    root: SequentialChoiceButton,
    chat_id: int,
    final_callback: Callable[[int, List[SequentialChoiceButton]], None],
  ):
    super().__init__()
    self._text = text
    self._current_node = root
    self._chat_id = chat_id
    self._final_callback = final_callback
    self._results: List[SequentialChoiceButton] = []
    self._buttons: List[ButtonNode] = []

  @property
  def page_type(self) -> Enum:
    return SequentialChoicePageType.main

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    self._buttons = []

    children = self._current_node.children

    for i, child in enumerate(children):
      self.register_button_handler(child, self._handle_step)
      self._buttons.append(child)

      if (i + 1) % self._current_node.max_children_per_row == 0 or (i + 1) == len(children):
        self._buttons.append(BreakButtonNode())

    if self._current_node.add_cancel_button:
      self._buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

  def _handle_step(self, navigator: TelebotPageNavigator, node: ButtonNode):
    if not isinstance(node, SequentialChoiceButton):
      return

    self._results.append(node)

    if not node.children:
      # End of the tree reached
      navigator.stop(self._text)
      self._final_callback(self._chat_id, self._results)
    else:
      # Move deeper and refresh the current message
      self._current_node = node
      navigator.update()

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._text} cancel")

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    text_lower = text.lower()
    for child in self._current_node.children:
      try:
        if int(child.text) == int(text):
          self._handle_step(navigator, child)
          return
      except Exception:
        if child.text.lower() == text_lower:
          self._handle_step(navigator, child)
          return

    raise RuntimeError("No such option")

  def get_goodbye_message(self) -> str:
    return f"{self._text} cancel"
