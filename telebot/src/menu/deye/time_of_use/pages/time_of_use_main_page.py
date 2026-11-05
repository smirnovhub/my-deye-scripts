import telebot

from enum import Enum
from typing import Union

from telebot_buttons import *
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_data_holder import TimeOfUseDataHolder
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page_type import TimeOfUsePageType
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseMainPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_data_holder: TimeOfUseDataHolder,
  ):
    super().__init__()
    self._tou_data_holder = tou_data_holder

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePageType.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return TimeOfUseHelper.get_time_of_use_as_rich_message(self._tou_data_holder.tou_data)

  def create_buttons(self) -> None:
    self.register_button(ButtonNode("Edit"), self._handle_edit)
    self.register_button(CancelButtonNode(), self._handle_cancel)

  async def _handle_edit(self, navigator: TelebotPageNavigator) -> None:
    tou_registers = await TimeOfUseHelper.read_time_of_use()
    tou_data = TimeOfUseHelper.get_time_of_use_data(tou_registers)
    self._tou_data_holder.actualize(tou_data)
    await navigator.navigate(TimeOfUsePageType.edit)

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop(
      TimeOfUseHelper.get_time_of_use_as_rich_message(
        self._tou_data_holder.tou_data,
        suffx = "cancel",
      ))

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return TimeOfUseHelper.get_time_of_use_as_rich_message(
      self._tou_data_holder.tou_data,
      suffx = "cancel",
    )
