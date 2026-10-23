import re
import telebot

from enum import Enum
from typing import Any, Union

from telebot_buttons import *
from time_of_use_helper import TimeOfUseHelper
from time_of_use_times import TimeOfUseTimes
from time_of_use_page import TimeOfUsePage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseHoursPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_times: TimeOfUseTimes,
    title: str,
    page_type: TimeOfUsePage,
    next_page_type: TimeOfUsePage,
  ):
    super().__init__()
    self._tou_times = tou_times
    self._title = title
    self._page_type = page_type
    self._next_page_type = next_page_type
    self._time_of_use_line_index = -1
    self._time_pattern = re.compile(r"(\d+):(\d+)")

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
    for i in range(24):
      if i > 0 and i % 4 == 0:
        self.register_button(BreakButtonNode())

      btn = ButtonNode(text = f"{i:02}")
      self.register_button(btn, self._create_hour_handler(i))

    self.register_button(BreakButtonNode())
    self.register_button(BackButtonNode(), self._handle_back)

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    match = self._time_pattern.match(text)
    if match:
      hour = int(match.group(1))
      minute = int(match.group(2))

      if not (0 <= hour <= 23):
        raise ValueError(f"Hour value should be from 0 to 23")

      if not (0 <= minute <= 55):
        raise ValueError(f"Minute value should be from 0 to 55")

      if minute % 5 != 0:
        raise ValueError('Minute should be a multiple of 5')

      await self._set_hour_and_minute_and_go_next(
        navigator = navigator,
        hour = hour,
        minute = minute,
      )
    else:
      try:
        hour = int(text)
      except Exception:
        raise ValueError(f"Hour value should be from 0 to 23")

      if not (0 <= hour <= 23):
        raise ValueError(f"Hour value should be from 0 to 23")

      await self._set_hour_and_go_next(
        navigator = navigator,
        hour = hour,
      )

  async def _handle_back(self, navigator: TelebotPageNavigator):
    await navigator.navigate(TimeOfUsePage.main)

  def _create_hour_handler(self, hour: int):
    async def handler(navigator: TelebotPageNavigator) -> None:
      await self._set_hour_and_go_next(navigator, hour)

    return handler

  async def _set_hour_and_go_next(
    self,
    navigator: TelebotPageNavigator,
    hour: int,
  ) -> None:
    self._tou_times.values[self._time_of_use_line_index].hour = hour
    await navigator.navigate(self._next_page_type, time_of_use_line_index = self._time_of_use_line_index)

  async def _set_hour_and_minute_and_go_next(
    self,
    navigator: TelebotPageNavigator,
    hour: int,
    minute: int,
  ) -> None:
    self._tou_times.values[self._time_of_use_line_index].hour = hour
    self._tou_times.values[self._time_of_use_line_index].minute = minute
    await navigator.navigate(TimeOfUsePage.main)
