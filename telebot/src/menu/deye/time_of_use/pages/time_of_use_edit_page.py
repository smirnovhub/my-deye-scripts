import telebot

from enum import Enum
from typing import Union

from deye_register import DeyeRegister
from time_of_use_ask_data import TimeOfUseAskData
from time_of_use_data_holder import TimeOfUseDataHolder
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page_type import TimeOfUsePageType
from time_of_use_week_buttons import TimeOfUseWeekButtons
from telebot_navigation_page import TelebotNavigationPage
from time_of_use_schedule_buttons import TimeOfUseScheduleButtons
from time_of_use_bottom_buttons import TimeOfUseBottomButtons

class TimeOfUseEditPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_register: DeyeRegister,
    tou_data_holder: TimeOfUseDataHolder,
  ):
    super().__init__()
    self._tou_register = tou_register
    self._tou_data_holder = tou_data_holder
    self._ask_data = TimeOfUseAskData()

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePageType.edit

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Time of Use schedule:"

  def create_buttons(self) -> None:
    week_buttons = TimeOfUseWeekButtons(self._tou_data_holder)
    schedule_buttons = TimeOfUseScheduleButtons(self._tou_data_holder)

    bottom_buttons = TimeOfUseBottomButtons(
      tou_register = self._tou_register,
      tou_data_holder = self._tou_data_holder,
      ask_data = self._ask_data,
    )

    week_buttons.create_buttons(page = self)
    schedule_buttons.create_buttons(page = self)
    bottom_buttons.create_buttons(
      page = self,
      can_save = schedule_buttons.is_data_correct,
    )

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return TimeOfUseHelper.get_time_of_use_as_rich_message(
      self._tou_data_holder.tou_original_data,
      suffx = "cancel",
    )
