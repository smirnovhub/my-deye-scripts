import asyncio
import telebot

from enum import Enum, auto
from typing import List, Union

from telebot_buttons import *
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
    result_future: asyncio.Future[ButtonNode],
    max_per_row: int = 5,
    max_lines_per_page: int = 5,
    edit_message_with_user_selection: bool = False,
  ):
    super().__init__()
    self._text = text
    self._options = options
    self._chat_id = chat_id
    self._result_future = result_future
    self._max_per_row = max_per_row
    self._max_lines_per_page = max_lines_per_page
    self._edit_message_with_user_selection = edit_message_with_user_selection
    self._current_page_index = 0
    self._items_per_page = self._max_lines_per_page * self._max_per_row
    self._total_pages = (len(self._options) + self._items_per_page - 1) // self._items_per_page

  @property
  def page_type(self) -> Enum:
    return AdvancedChoicePageType.main

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
    """
    Logic for building the current page of options.
    """
    start = self._current_page_index * self._items_per_page
    end = start + self._items_per_page

    # Re-instantiate clean ButtonNode objects from options to avoid key mutation issues
    page_items = [
      ButtonNode(
        text = opt.text,
        data = opt.data,
        style = opt.style,
        key = opt.key,
      ) for opt in self._options[start:end]
    ]

    # Add option buttons to grid layout with max_per_row logic
    for i, button in enumerate(page_items):
      self.register_button(button, self._handle_selection)

      # Add break if row is full or it is the last item
      if (i + 1) % self._max_per_row == 0 or (i + 1) == len(page_items):
        self.register_button(BreakButtonNode())

    # Add empty placeholders for grid alignment if multiple pages exist
    if self._total_pages > 1:
      empty_slots = self._items_per_page - len(page_items)
      for i in range(empty_slots):
        dummy_button = ButtonNode(" ")
        self.register_button(dummy_button, handler = None)

        if (len(page_items) + i + 1) % self._max_per_row == 0 or i == empty_slots - 1:
          self.register_button(BreakButtonNode())

    # Add navigation row if multiple pages exist
    if self._total_pages > 1:
      self.register_button(ButtonNode("Prev"), self._move_prev)

      self.register_button(
        ButtonNode(f"{self._current_page_index + 1}/{self._total_pages}"),
        self._move_next,
      )

      self.register_button(ButtonNode("Next"), self._move_next)
      self.register_button(BreakButtonNode())

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    if not self._result_future.done():
      self._result_future.set_result(ButtonNode(text = text))

    final_text = f"{self._text} {text}" if self._edit_message_with_user_selection else self._text
    await navigator.stop(final_text)

  async def _move_next(self, navigator: TelebotPageNavigator) -> None:
    self._current_page_index = (self._current_page_index + 1) % self._total_pages
    await navigator.update()

  async def _move_prev(self, navigator: TelebotPageNavigator) -> None:
    self._current_page_index = (self._current_page_index - 1) % self._total_pages
    await navigator.update()

  async def _handle_selection(self, navigator: TelebotPageNavigator, button: ButtonNode):
    if not self._result_future.done():
      self._result_future.set_result(button)

    final_text = f"{self._text} {button.text}" if self._edit_message_with_user_selection else self._text
    await navigator.stop(final_text)

  async def on_stop(self) -> None:
    if not self._result_future.done():
      self._result_future.cancel()

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._text} cancel"

  def get_stop_by_command_message(self, command: str) -> Union[str, telebot.types.InputRichMessage]:
    _, _, param = command.partition(' ')
    return f"{self._text} {param.replace('_', ' ')}"
