import asyncio
import telebot

from enum import Enum, auto
from typing import Union

from telebot_buttons import *
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator

class CountdownWithCancelPageType(Enum):
  main = auto()

class CountdownWithCancelPage(TelebotNavigationPage):
  def __init__(
    self,
    chat_id: int,
    text: Union[str, telebot.types.InputRichMessage],
    seconds: int,
    result_future: asyncio.Future[bool],
  ):
    super().__init__()
    self._chat_id = chat_id
    self._text = text
    self._seconds = seconds
    self._result_future = result_future

  @property
  def page_type(self) -> Enum:
    return CountdownWithCancelPageType.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._text} {self._seconds}"

  @property
  def need_user_input(self) -> bool:
    return True

  @property
  def resend_message_on_user_input(self) -> bool:
    return False

  def create_buttons(self) -> None:
    self.register_button(CancelButtonNode(), self._handle_cancel)

  async def _handle_cancel(self, navigator: TelebotPageNavigator):
    if not self._result_future.done():
      self._result_future.set_result(False)
    await navigator.stop(delete_message = True)

  async def on_auto_update(self, navigator: TelebotPageNavigator) -> None:
    self._seconds -= 1
    if self._seconds <= 0:
      if not self._result_future.done():
        self._result_future.set_result(True)
      await navigator.stop(delete_message = True)
    else:
      await navigator.update()

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    if not self._result_future.done():
      self._result_future.set_result(False)
    await navigator.stop(delete_message = True)

  async def on_stop(self) -> None:
    if not self._result_future.done():
      self._result_future.set_result(False)

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._text} cancel"
