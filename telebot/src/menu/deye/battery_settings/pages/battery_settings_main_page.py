import copy

from enum import Enum
from typing import List

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
  ):
    super().__init__()
    self._batt_data = batt_data
    self._batt_data_original = copy.deepcopy(batt_data)
    self._shutdown_soc_register = shutdown_soc_register
    self._low_batt_soc_register = low_batt_soc_register
    self._restart_soc_register = restart_soc_register

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

    buttons.append(
      self.register_button_handler(
        ButtonNode("Shutdown"),
        self._create_navigation_handler(BatterySettingsPage.shutdown_soc),
      ))

    shutdown_soc = ButtonNode(text = f"{self._batt_data.shutdown_soc}%")
    buttons.append(
      self.register_button_handler(
        shutdown_soc,
        self._create_navigation_handler(BatterySettingsPage.shutdown_soc),
      ))

    buttons.append(BreakButtonNode())

    buttons.append(
      self.register_button_handler(
        ButtonNode("Low Batt"),
        self._create_navigation_handler(BatterySettingsPage.low_batt_soc),
      ))

    low_batt_soc = ButtonNode(text = f"{self._batt_data.low_batt_soc}%")
    buttons.append(
      self.register_button_handler(
        low_batt_soc,
        self._create_navigation_handler(BatterySettingsPage.low_batt_soc),
      ))

    buttons.append(BreakButtonNode())

    buttons.append(
      self.register_button_handler(
        ButtonNode("Restart"),
        self._create_navigation_handler(BatterySettingsPage.restart_soc),
      ))

    restart_soc = ButtonNode(text = f"{self._batt_data.restart_soc}%")
    buttons.append(
      self.register_button_handler(
        restart_soc,
        self._create_navigation_handler(BatterySettingsPage.restart_soc),
      ))

    buttons.append(BreakButtonNode())

    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop()

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    navigator.stop()

  def _create_navigation_handler(self, target_page: Enum):
    # The handler now accepts both navigator and button_node
    def handler(navigator: TelebotPageNavigator) -> None:
      navigator.navigate(target_page)

    return handler
