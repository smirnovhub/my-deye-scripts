import telebot

from enum import Enum
from typing import Any, Union

from telebot_buttons import *
from time_of_use_helper import TimeOfUseHelper
from time_of_use_times import TimeOfUseTimes
from time_of_use_page import TimeOfUsePage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseMinutesPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_times: TimeOfUseTimes,
    title: str,
    page_type: TimeOfUsePage,
  ):
    super().__init__()
    self._tou_times = tou_times
    self._title = title
    self._page_type = page_type
    self._time_of_use_line_index = -1

  @property
  def page_type(self) -> Enum:
    return self._page_type

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return self._title

  @property
  def need_user_input(self) -> bool:
    return True

  async def on_navigate(
    self,
    navigator: TelebotPageNavigator,
    **kwargs: Any,
  ) -> None:
    index = kwargs.get("time_of_use_line_index")
    if index is None:
      raise RuntimeError("time_of_use_line_index not found")

    TimeOfUseHelper.check_bounds(self._tou_times.values, index)
    self._time_of_use_line_index = index

  def create_buttons(self) -> None:
    minutes = list(range(0, 60, 5))

    for i, minute in enumerate(minutes):
      if i > 0 and i % 4 == 0:
        self.register_button(BreakButtonNode())

      btn = ButtonNode(text = f"{minute:02}")
      self.register_button(btn, self._create_minute_handler(minute))

    self.register_button(BreakButtonNode())
    self.register_button(BackButtonNode(), self._handle_back)

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    try:
      minute = int(text)
    except Exception:
      raise ValueError(f"Minute value should be from 0 to 55")

    if not (0 <= minute <= 55):
      raise ValueError(f"Minute value should be from 0 to 55")

    if minute % 5 != 0:
      raise ValueError('Minute should be a multiple of 5')

    await self._set_minute_and_go_back(
      navigator = navigator,
      minute = minute,
    )

  async def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    await navigator.navigate(TimeOfUsePage.main)

  def _create_minute_handler(self, minute: int):
    async def handler(navigator: TelebotPageNavigator) -> None:
      await self._set_minute_and_go_back(navigator, minute)

    return handler

  async def _set_minute_and_go_back(
    self,
    navigator: TelebotPageNavigator,
    minute: int,
  ) -> None:
    self._tou_times.values[self._time_of_use_line_index].minute = minute
    await navigator.navigate(TimeOfUsePage.main)
