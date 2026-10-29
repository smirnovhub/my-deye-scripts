import copy
import telebot

from enum import Enum
from typing import Any, Union
from datetime import timedelta

from telebot_buttons import *
from deye_register import DeyeRegister
from deye_loggers import DeyeLoggers
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_ask_data import TimeOfUseAskData
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page_type import TimeOfUsePageType
from time_of_use_data import TimeOfUseData
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseUndoPage(TelebotNavigationPage):
  def __init__(
    self,
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._tou_register = tou_register
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)
    self._loggers = DeyeLoggers()
    self._ask_data = TimeOfUseAskData()

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePageType.undo

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return TimeOfUseHelper.get_time_of_use_as_rich_message(self._tou_data, suffx = "saved")

  async def on_navigate(
    self,
    navigator: TelebotPageNavigator,
    **kwargs: Any,
  ) -> None:
    await navigator.add_delayed_action(
      delay = timedelta(minutes = 5),
      action = lambda: navigator.stop(self._get_done_text()),
    )

  def create_buttons(self) -> None:
    if self._ask_data.ask_for_undo:
      self.register_button(ButtonNode("Really want to undo?"))
      self.register_button(BreakButtonNode())
      self.register_button(ButtonNode("Yes"), self._handle_undo_yes)
      self.register_button(ButtonNode("No"), self._handle_undo_no)
    else:
      self.register_button(ButtonNode("Undo"), self._handle_undo)
      self.register_button(ButtonNode("Done"), self._handle_done)

  async def _handle_undo(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_undo = True
    await navigator.update()

  async def _handle_undo_no(self, navigator: TelebotPageNavigator) -> None:
    self._ask_data.ask_for_undo = False
    await navigator.update()

  async def _handle_undo_yes(self, navigator: TelebotPageNavigator) -> None:
    data = TimeOfUseHelper.get_cleared_unchanged_data(
      data_to_clear = self._tou_original_data,
      original_data = self._tou_data,
    )

    await TimeOfUseHelper.write_time_of_use(
      tou_register = self._tou_register,
      master_logger = self._loggers.master,
      tou_data = data,
    )

    text = TimeOfUseHelper.get_time_of_use_as_rich_message(
      tou_data = self._tou_original_data,
      suffx = "undone",
    )

    await navigator.stop(text)

  async def _handle_done(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop(self._get_done_text())

  def get_goodbye_message(self) -> Union[str, telebot.types.InputRichMessage]:
    return self._get_done_text()

  def _get_done_text(self) -> telebot.types.InputRichMessage:
    return TimeOfUseHelper.get_time_of_use_as_rich_message(
      self._tou_data,
      suffx = "done",
    )
