import copy
import telebot

from enum import Enum
from typing import Union

from deye_register import DeyeRegister
from time_of_use_ask_data import TimeOfUseAskData
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page import TimeOfUsePage
from time_of_use_data import TimeOfUseData
from time_of_use_week_buttons import TimeOfUseWeekButtons
from telebot_navigation_page import TelebotNavigationPage
from time_of_use_schedule_buttons import TimeOfUseScheduleButtons
from time_of_use_bottom_buttons import TimeOfUseBottomButtons

class TimeOfUseMainPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._tou_register = tou_register
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)
    self._ask_data = TimeOfUseAskData()

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Time of Use schedule:"

  def create_buttons(self) -> None:
    week_buttons = TimeOfUseWeekButtons(tou_week = self._tou_data.week)
    schedule_buttons = TimeOfUseScheduleButtons(tou_data = self._tou_data)

    bottom_buttons = TimeOfUseBottomButtons(
      tou_register = self._tou_register,
      tou_data = self._tou_data,
      tou_original_data = self._tou_original_data,
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
      self._tou_original_data,
      suffx = "cancel",
    )
