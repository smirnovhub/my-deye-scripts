import telebot

from enum import Enum
from typing import Union

from telebot_buttons import *
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page import TimeOfUsePage
from time_of_use_data import TimeOfUseData
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseMainPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._tou_data = tou_data

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return TimeOfUseHelper.get_time_of_use_as_rich_message(self._tou_data, )

  def create_buttons(self) -> None:
    self.register_button(ButtonNode("Edit"), self._handle_edit)
    self.register_button(CancelButtonNode(), self._handle_cancel)

  async def _handle_edit(self, navigator: TelebotPageNavigator) -> None:
    await navigator.navigate(TimeOfUsePage.edit)

  async def _handle_cancel(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop(TimeOfUseHelper.get_time_of_use_as_rich_message(
      self._tou_data,
      suffx = "cancel",
    ))

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return TimeOfUseHelper.get_time_of_use_as_rich_message(
      self._tou_data,
      suffx = "cancel",
    )
