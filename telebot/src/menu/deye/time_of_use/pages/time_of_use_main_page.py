import copy

from enum import Enum
from typing import List

from button_node import ButtonNode
from deye_register import DeyeRegister
from telebot_async_runner import TelebotAsyncRunner
from time_of_use_ask_data import TimeOfUseAskData
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page import TimeOfUsePage
from time_of_use_data import TimeOfUseData
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_week_buttons import TimeOfUseWeekButtons
from telebot_navigation_page import TelebotNavigationPage
from time_of_use_schedule_buttons import TimeOfUseScheduleButtons
from time_of_use_bottom_buttons import TimeOfUseBottomButtons

class TimeOfUseMainPage(TelebotNavigationPage):
  def __init__(
    self,
    runner: TelebotAsyncRunner,
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
  ):
    super().__init__(runner)
    self._tou_register = tou_register
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)
    self._ask_data = TimeOfUseAskData()

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  @property
  def need_user_input(self) -> bool:
    return False

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    week_buttons = TimeOfUseWeekButtons(
      page = self,
      tou_week = self._tou_data.week,
    )

    schedule_buttons = TimeOfUseScheduleButtons(
      page = self,
      tou_data = self._tou_data,
    )

    bottom_buttons = TimeOfUseBottomButtons(
      page = self,
      tou_register = self._tou_register,
      tou_data = self._tou_data,
      tou_original_data = self._tou_original_data,
      ask_data = self._ask_data,
      can_save = schedule_buttons.is_data_correct,
    )

    self._buttons = week_buttons.buttons + schedule_buttons.buttons + bottom_buttons.buttons

  def on_user_input(self, navigator: TelebotPageNavigator, text: str) -> None:
    text = TimeOfUseHelper.get_time_of_use_as_text(self._tou_original_data)
    navigator.stop(text)

  def get_goodbye_message(self) -> str:
    return TimeOfUseHelper.get_time_of_use_as_text(self._tou_original_data)
