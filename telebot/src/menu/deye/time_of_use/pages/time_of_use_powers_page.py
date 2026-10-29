import telebot

from enum import Enum
from typing import Union

from telebot_buttons import *
from time_of_use_data import TimeOfUsePowers
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page_type import TimeOfUsePageType
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUsePowersPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_powers: TimeOfUsePowers,
  ):
    super().__init__()
    self._tou_powers = tou_powers
    self._time_of_use_line_index = -1
    self._powers = [
      [0, 250, 500],
      [1000, 1250, 1500],
      [2000, 2500, 3000],
      [3500, 4000, 4500],
      [5000, 5500, 6000],
    ]
    self._min_val = min(x for row in self._powers for x in row)
    self._max_val = max(x for row in self._powers for x in row)

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePageType.powers

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Battery power, W:"

  @property
  def need_user_input(self) -> bool:
    return True

  async def on_navigate( # type: ignore[override]
      self, navigator: TelebotPageNavigator, *, time_of_use_line_index: int) -> None:
    TimeOfUseHelper.check_upper_bounds(self._tou_powers.values, time_of_use_line_index)
    self._time_of_use_line_index = time_of_use_line_index

  def create_buttons(self) -> None:
    old_value = -1
    if self._time_of_use_line_index < 0:
      first_item = self._tou_powers.values[0]
      if all(x == first_item for x in self._tou_powers.values):
        old_value = first_item
    else:
      old_value = self._tou_powers.values[self._time_of_use_line_index]

    for row_index, row in enumerate(self._powers):
      if row_index > 0:
        self.register_button(BreakButtonNode())

      for power in row:
        style = ButtonStyle.default
        if power == old_value:
          style = ButtonStyle.success

        btn = ButtonNode(text = str(power), style = style)
        self.register_button(btn, self._create_power_handler(power))

    self.register_button(BreakButtonNode())
    self.register_button(BackButtonNode(), self._handle_back)

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    try:
      power = int(text)
    except Exception:
      raise ValueError(f"Power value should be from {self._min_val} to {self._max_val}")

    if not (self._min_val <= power <= self._max_val):
      raise ValueError(f"Power value should be from {self._min_val} to {self._max_val}")

    await self._set_power_and_go_back(
      navigator = navigator,
      power = power,
    )

  async def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    await navigator.navigate(TimeOfUsePageType.edit)

  def _create_power_handler(self, power: int):
    async def handler(navigator: TelebotPageNavigator) -> None:
      await self._set_power_and_go_back(navigator, power)

    return handler

  async def _set_power_and_go_back(
    self,
    navigator: TelebotPageNavigator,
    power: int,
  ) -> None:
    if self._time_of_use_line_index < 0:
      # Replace all elements in the list with the new value
      self._tou_powers.values[:] = [power] * len(self._tou_powers.values)
    else:
      self._tou_powers.values[self._time_of_use_line_index] = power

    await navigator.navigate(TimeOfUsePageType.edit)
