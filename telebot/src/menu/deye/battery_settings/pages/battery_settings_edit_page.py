import copy
import telebot

from enum import Enum
from typing import Union

from telebot_buttons import *
from telebot_utils import TelebotUtils
from button_style import ButtonStyle
from deye_loggers import DeyeLoggers
from battery_settings_helper import BatterySettingsHelper
from battery_settings_data import BatterySettingsData
from battery_settings_page_type import BatterySettingsPageType
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage
from telebot_deye_helper import TelebotDeyeHelper
from deye_registers_holder_async import DeyeRegistersHolderAsync
from battery_settings_registers import BatterySettingsRegisters

class BatterySettingsEditPage(TelebotNavigationPage):
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
    return BatterySettingsPageType.edit

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return self._title

  @property
  def need_user_input(self) -> bool:
    return True

  def create_buttons(self) -> None:
    value = 0
    style = ButtonStyle.default

    for page, val in self._batt_data.values.items():
      if val < value:
        style = ButtonStyle.danger

      self._make_buttons(
        page_type = page,
        title = page.name,
        style = style,
      )
      value = val

    if self._need_save():
      self.register_button(ButtonNode("Save"), self._handle_save)

    self.register_button(CancelButtonNode(), self._handle_cancel)

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return BatterySettingsHelper.get_data_as_rich_message(
      title = f"{self._title} cancel",
      values = self._batt_data_original_values,
    )

  def _make_buttons(
    self,
    page_type: BatterySettingsPageType,
    title: str,
    style: ButtonStyle,
  ) -> None:
    button = ButtonNode(
      text = f"{self._batt_data.values[page_type]}%",
      style = style,
      key = f"{page_type}",
    )
    self.register_button(ButtonNode(text = title, style = style), self._create_navigation_handler(page_type))
    self.register_button(button, self._create_navigation_handler(page_type))
    self.register_button(BreakButtonNode())

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop(
      BatterySettingsHelper.get_data_as_rich_message(
        title = f"{self._title} cancel",
        values = self._batt_data_original_values,
      ))

  async def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    await navigator.stop(
      BatterySettingsHelper.get_data_as_rich_message(
        title = self._title,
        values = self._batt_data_original_values,
      ))

  def _create_navigation_handler(self, target_page: Enum):
    async def handler(navigator: TelebotPageNavigator) -> None:
      await navigator.navigate(target_page)

    return handler

  def _need_save(self) -> bool:
    return self._batt_data.values != self._batt_data_original_values

  async def _handle_save(self, navigator: TelebotPageNavigator) -> None:
    try:
      holder = DeyeRegistersHolderAsync(
        loggers = [self._loggers.master],
        register_creator = lambda prefix: BatterySettingsRegisters(prefix),
        **TelebotDeyeHelper.holder_kwargs,
      )

      await holder.read_registers()

      registers = holder.master_registers

      for register in self._batt_data.registers.values():
        reg = registers.get_register_by_name(register.name)
        if reg.value != register.value:
          raise ValueError(f"{reg.description} was changed unexpectedly since last read")

      for page, value in self._batt_data.values.items():
        register = self._batt_data.registers[page]
        reg = registers.get_register_by_name(register.name)
        if reg.value != value:
          await holder.write_register(register, value)

      message = BatterySettingsHelper.get_data_as_rich_message(
        title = f"{self._title} saved",
        values = self._batt_data.values,
      )
      await navigator.stop(message)

    except Exception as e:
      await navigator.stop(f"{self._title} {TelebotUtils.escape_html(str(e))}")
    finally:
      holder.disconnect()
