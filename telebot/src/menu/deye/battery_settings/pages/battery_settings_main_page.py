import copy

from enum import Enum
from typing import List

from dataclasses import asdict
from button_node import ButtonNode
from deye_register import DeyeRegister
from break_button_node import BreakButtonNode
from battery_settings_data import BatterySettingsData
from battery_settings_page import BatterySettingsPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class BatterySettingsMainPage(TelebotNavigationPage):
  def __init__(
    self,
    batt_data: BatterySettingsData,
    shutdown_soc_register: DeyeRegister,
    low_batt_soc_register: DeyeRegister,
    restart_soc_register: DeyeRegister,
    title: str,
  ):
    super().__init__()
    self._batt_data = batt_data
    self._batt_data_original = copy.deepcopy(batt_data)
    self._shutdown_soc_register = shutdown_soc_register
    self._low_batt_soc_register = low_batt_soc_register
    self._restart_soc_register = restart_soc_register
    self._title = title

  @property
  def page_type(self) -> Enum:
    return BatterySettingsPage.main

  @property
  def need_user_input(self) -> bool:
    return False

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    buttons: List[ButtonNode] = []

    buttons.extend(self._get_buttons(
      page_type = BatterySettingsPage.shutdown_soc,
      title = "Shutdown",
    ))

    buttons.append(BreakButtonNode())

    buttons.extend(self._get_buttons(
      page_type = BatterySettingsPage.low_batt_soc,
      title = "Low Batt",
    ))

    buttons.append(BreakButtonNode())

    buttons.extend(self._get_buttons(
      page_type = BatterySettingsPage.restart_soc,
      title = "Restart",
    ))

    buttons.append(BreakButtonNode())

    if self._need_save():
      buttons.append(self.register_button_handler(ButtonNode("Save"), self._handle_save))

    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def _get_buttons(self, page_type: BatterySettingsPage, title: str) -> List[ButtonNode]:
    button = ButtonNode(text = f"{self._batt_data.values[page_type]}%")
    return [
      self.register_button_handler(ButtonNode(title), self._create_navigation_handler(page_type)),
      self.register_button_handler(button, self._create_navigation_handler(page_type)),
    ]

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} cancel")

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    navigator.stop(f"{self._title} cancel")

  def _create_navigation_handler(self, target_page: Enum):
    # The handler now accepts both navigator and button_node
    def handler(navigator: TelebotPageNavigator) -> None:
      navigator.navigate(target_page)

    return handler

  def _need_save(self) -> bool:
    return asdict(self._batt_data) != asdict(self._batt_data_original)

  def _handle_save(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title} saved")

  def get_goodbye_message(self) -> str:
    return f"{self._title} cancel"
