import telebot

from enum import Enum
from typing import Union

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
    prev_page_type: TimeOfUsePage,
  ):
    super().__init__()
    self._tou_times = tou_times
    self._title = title
    self._page_type = page_type
    self._prev_page_type = prev_page_type
    self._time_of_use_line_index = -1
    self._selected_hour = -1

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
    *,
    time_of_use_line_index: int,
    selected_hour: int,
  ) -> None:
    TimeOfUseHelper.check_bounds(self._tou_times.values, time_of_use_line_index)
    self._time_of_use_line_index = time_of_use_line_index
    self._selected_hour = selected_hour

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
    await navigator.navigate(
      self._prev_page_type,
      time_of_use_line_index = self._time_of_use_line_index,
    )

  def _create_minute_handler(self, minute: int):
    async def handler(navigator: TelebotPageNavigator) -> None:
      await self._set_minute_and_go_back(navigator, minute)

    return handler

  async def _set_minute_and_go_back(
    self,
    navigator: TelebotPageNavigator,
    minute: int,
  ) -> None:
    TimeOfUseHelper.check_bounds(self._tou_times.values, self._time_of_use_line_index)
    self._tou_times.values[self._time_of_use_line_index].hour = self._selected_hour
    self._tou_times.values[self._time_of_use_line_index].minute = minute
    await navigator.navigate(TimeOfUsePage.edit)
