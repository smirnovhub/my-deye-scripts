import asyncio
import telebot

from enum import Enum, auto
from typing import List, Union

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
    result_future: asyncio.Future[List[SequentialChoiceButton]],
  ):
    super().__init__()
    self._text = text
    self._current_node = root
    self._chat_id = chat_id
    self._result_future = result_future
    self._results: List[SequentialChoiceButton] = []

  @property
  def page_type(self) -> Enum:
    return SequentialChoicePageType.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return self._text

  @property
  def need_user_input(self) -> bool:
    return True

  def create_buttons(self) -> None:
    print(self._current_node)
    children = self._current_node.children

    for i, child in enumerate(children):
      self.register_button(child, self._handle_step)

      if (i + 1) % self._current_node.max_children_per_row == 0 or (i + 1) == len(children):
        self.register_button(BreakButtonNode())

    if self._current_node.add_cancel_button:
      self.register_button(ButtonNode("Cancel"), self._handle_cancel)

  async def _handle_step(self, navigator: TelebotPageNavigator, node: ButtonNode):
    if not isinstance(node, SequentialChoiceButton):
      raise ValueError("Button type should be SequentialChoiceButton")

    self._results.append(node)

    if not node.children and not self._result_future.done():
      # End of the tree reached
      self._result_future.set_result(self._results)
      navigator.stop(self._text)
    else:
      # Move deeper and refresh the current message
      self._current_node = node
      await navigator.update()

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._text} cancel")

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    text_lower = text.lower()
    for child in self._current_node.children:
      try:
        if int(child.text) == int(text):
          await self._handle_step(navigator, child)
          return
      except Exception:
        if child.text.lower() == text_lower:
          await self._handle_step(navigator, child)
          return

    raise RuntimeError("No such option")

  def on_stop(self):
    if not self._result_future.done():
      self._result_future.cancel()

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._text} cancel"
