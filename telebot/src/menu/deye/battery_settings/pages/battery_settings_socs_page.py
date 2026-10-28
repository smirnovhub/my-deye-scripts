import telebot

from enum import Enum
from typing import List, Union

from telebot_buttons import *
from battery_settings_data import BatterySettingsData
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from battery_settings_page_type import BatterySettingsPageType

class BatterySettingsSocsPage(TelebotNavigationPage):
  def __init__(
    self,
    page_type: BatterySettingsPageType,
    batt_data: BatterySettingsData,
  ):
    super().__init__()
    self._page_type = page_type
    self._batt_data = batt_data
    self._row_length = 4
    self._min_value = 0
    self._max_value = 0

  @property
  def page_type(self) -> Enum:
    return self._page_type

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return f"{self._page_type.title}, %:"

  @property
  def need_user_input(self) -> bool:
    return True

  def create_buttons(self) -> None:
    self._min_value, self._max_value = self._batt_data.get_bounds(self._page_type)

    values = self._generate_values(
      min_value = self._min_value,
      max_value = self._max_value,
      count = 20,
    )

    for index, value in enumerate(values):
      if index > 0 and (index % self._row_length) == 0:
        self.register_button(BreakButtonNode())

      btn = ButtonNode(text = str(value))
      self.register_button(btn, self._create_soc_handler(value))

    self.register_button(BreakButtonNode())
    self.register_button(BackButtonNode(), self._handle_back)

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    try:
      soc = int(text)
    except Exception:
      raise ValueError(f"{self._page_type.title} value should be from {self._min_value} to {self._max_value}")

    if not (self._min_value <= soc <= self._max_value):
      raise ValueError(f"{self._page_type.title} value should be from {self._min_value} to {self._max_value}")

    await self._set_soc_and_go_back(
      navigator = navigator,
      soc = soc,
    )

  async def _handle_back(self, navigator: TelebotPageNavigator) -> None:
    await navigator.navigate(BatterySettingsPageType.edit)

  def _create_soc_handler(self, soc: int):
    async def handler(navigator: TelebotPageNavigator) -> None:
      await self._set_soc_and_go_back(navigator, soc)

    return handler

  async def _set_soc_and_go_back(
    self,
    navigator: TelebotPageNavigator,
    soc: int,
  ) -> None:
    if not (self._min_value <= soc <= self._max_value):
      raise ValueError(f"{self._page_type.title} value should be from {self._min_value} to {self._max_value}")

    self._batt_data.values[self._page_type] = soc
    await navigator.navigate(BatterySettingsPageType.edit)

  def _generate_values(
    self,
    min_value: int,
    max_value: int,
    count: int,
  ) -> List[int]:
    # Generate the initial full range of integers
    full_range = list(range(min_value, max_value + 1))
    current_len = len(full_range)

    # If the range is already smaller or equal to count, return it as is
    if current_len <= count:
      return full_range

    # Calculate how many elements need to be removed
    to_remove = current_len - count

    # To remove elements evenly, we divide the range into (to_remove + 1) parts.
    # The indices to be removed are located at these "split points".
    step = current_len / (to_remove + 1)

    # Calculate indices from the end to the beginning to avoid index shifting during deletion
    indices_to_remove = [int(i * step) for i in range(1, to_remove + 1)]

    # Remove elements at calculated indices
    for index in reversed(indices_to_remove):
      full_range.pop(index)

    return full_range
