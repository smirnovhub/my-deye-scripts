import asyncio
import telebot

from enum import Enum, auto
from typing import List, Union

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator

class UserChoicePageType(Enum):
  main = auto()

class UserChoicePage(TelebotNavigationPage):
  def __init__(
    self,
    text: Union[str, telebot.types.InputRichMessage],
    options: List[ButtonNode],
    chat_id: int,
    result_future: asyncio.Future[ButtonNode],
    max_per_row: int = 5,
    accept_wrong_choice_from_user_input: bool = False,
    wrong_choice_text: str = 'No such option',
  ):
    super().__init__()
    self._text = text
    self._options = options
    self._chat_id = chat_id
    self._result_future = result_future
    self._max_per_row = max_per_row
    self._accept_wrong_choice_from_user_input = accept_wrong_choice_from_user_input
    self._wrong_choice_text = wrong_choice_text

  @property
  def page_type(self) -> Enum:
    return UserChoicePageType.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return self._text

  @property
  def need_user_input(self) -> bool:
    return True

  @property
  def resend_message_on_user_input(self) -> bool:
    return False

  def create_buttons(self) -> None:
    # Iterate with index to manage rows
    for i, button in enumerate(self._options):
      self.register_button(button, self._handle_selection)

      # Add a break if we reached the max items per row OR if it's the last item
      if (i + 1) % self._max_per_row == 0 or (i + 1) == len(self._options):
        self.register_button(BreakButtonNode())

  async def _handle_selection(self, navigator: TelebotPageNavigator, button: ButtonNode):
    if not self._result_future.done():
      self._result_future.set_result(button)
    await navigator.stop()

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    text_lower = text.lower()
    for button in self.buttons:
      if button.text.lower() == text_lower:
        if not self._result_future.done():
          self._result_future.set_result(button)
        await navigator.stop()
        return

    if self._accept_wrong_choice_from_user_input:
      if not self._result_future.done():
        self._result_future.set_result(ButtonNode(text = text))
      await navigator.stop()
    else:
      await navigator.send_message(self._wrong_choice_text)
      await navigator.stop()

  def on_stop(self):
    if not self._result_future.done():
      self._result_future.cancel()
