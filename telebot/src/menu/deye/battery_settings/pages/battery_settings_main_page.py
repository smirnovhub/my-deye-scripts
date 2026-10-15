import copy
import telebot

from enum import Enum
from typing import List, Union

from button_node import ButtonNode
from battery_settings_helper import BatterySettingsHelper
from battery_settings_data import BatterySettingsData
from battery_settings_page import BatterySettingsPage
from telebot_async_runner import TelebotAsyncRunner
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class BatterySettingsMainPage(TelebotNavigationPage):
  def __init__(
    self,
    runner: TelebotAsyncRunner,
    batt_data: BatterySettingsData,
    title: str,
  ):
    super().__init__(runner)
    self._batt_data_original_values = copy.deepcopy(batt_data.values)
    self._title = title

  @property
  def page_type(self) -> Enum:
    return BatterySettingsPage.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return BatterySettingsHelper.get_data_as_rich_message(
      title = self._title,
      values = self._batt_data_original_values,
    )

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    buttons: List[ButtonNode] = []

    buttons.append(self.register_button_handler(ButtonNode("Edit"), self._handle_edit))
    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return BatterySettingsHelper.get_data_as_rich_message(
      title = f"{self._title} cancel",
      values = self._batt_data_original_values,
    )

  def _handle_edit(self, navigator: TelebotPageNavigator) -> None:
    navigator.navigate(BatterySettingsPage.edit)

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(
      BatterySettingsHelper.get_data_as_rich_message(
        title = f"{self._title} cancel",
        values = self._batt_data_original_values,
      ))
