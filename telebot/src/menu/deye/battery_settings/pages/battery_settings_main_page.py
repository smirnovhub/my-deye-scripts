import copy

from enum import Enum
from typing import List

from button_node import ButtonNode
from deye_loggers import DeyeLoggers
from break_button_node import BreakButtonNode
from battery_settings_data import BatterySettingsData
from battery_settings_page import BatterySettingsPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from telebot_deye_helper import TelebotDeyeHelper
from deye_registers_holder import DeyeRegistersHolder, Dict
from battery_settings_registers import BatterySettingsRegisters

class BatterySettingsMainPage(TelebotNavigationPage):
  def __init__(
    self,
    batt_data: BatterySettingsData,
    title: str,
  ):
    super().__init__()
    self._loggers = DeyeLoggers()
    self._batt_data = batt_data
    self._batt_data_original_values = copy.deepcopy(batt_data.values)
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

    for page in self._batt_data.values.keys():
      buttons.extend(self._get_buttons(page_type = page, title = page.name))
      buttons.append(BreakButtonNode())

    if self._need_save():
      buttons.append(self.register_button_handler(ButtonNode("Save"), self._handle_save))

    buttons.append(self.register_button_handler(ButtonNode("Cancel"), self._handle_cancel))

    self._buttons = buttons

  def get_goodbye_message(self) -> str:
    return f"{self._title}\n{self._get_data_as_text(self._batt_data_original_values)}"

  def _get_buttons(self, page_type: BatterySettingsPage, title: str) -> List[ButtonNode]:
    button = ButtonNode(text = f"{self._batt_data.values[page_type]}%")
    return [
      self.register_button_handler(ButtonNode(title), self._create_navigation_handler(page_type)),
      self.register_button_handler(button, self._create_navigation_handler(page_type)),
    ]

  def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop(f"{self._title}\n{self._get_data_as_text(self._batt_data_original_values)}")

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    navigator.stop(f"{self._title}\n{self._get_data_as_text(self._batt_data_original_values)}")

  def _create_navigation_handler(self, target_page: Enum):
    def handler(navigator: TelebotPageNavigator) -> None:
      navigator.navigate(target_page)

    return handler

  def _need_save(self) -> bool:
    return self._batt_data.values != self._batt_data_original_values

  def _handle_save(self, navigator: TelebotPageNavigator) -> None:
    try:
      holder = DeyeRegistersHolder(
        loggers = [self._loggers.master],
        register_creator = lambda prefix: BatterySettingsRegisters(prefix),
        **TelebotDeyeHelper.holder_kwargs,
      )

      holder.read_registers()

      registers = holder.master_registers

      for register in self._batt_data.registers.values():
        reg = registers.get_register_by_name(register.name)
        if reg.value != register.value:
          raise ValueError(f"{reg.description} was changed unexpectedly since last read")

      for page, value in self._batt_data.values.items():
        register = self._batt_data.registers[page]
        reg = registers.get_register_by_name(register.name)
        if reg.value != value:
          holder.write_register(register, value)

      navigator.stop(f"{self._title}\n{self._get_data_as_text(self._batt_data.values)}")

    except Exception as ee:
      navigator.stop(f"{self._title} {str(ee)}")
    finally:
      holder.disconnect()

  def _get_data_as_text(self, values: Dict[BatterySettingsPage, int]) -> str:
    result = "<pre>"
    for page, value in values.items():
      result += f"{page.title}: {value}%\n"
    return f"{result}</pre>"
