import copy
import telebot

from enum import Enum
from typing import Union

from telebot_buttons import *
from deye_register import DeyeRegister
from telebot_utils import TelebotUtils
from time_of_use_data_holder import TimeOfUseDataHolder
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page_type import TimeOfUsePageType
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseEnablePage(TelebotNavigationPage):
  def __init__(
    self,
    tou_register: DeyeRegister,
    tou_data_holder: TimeOfUseDataHolder,
  ):
    super().__init__()
    self._tou_register = tou_register
    self._tou_data_holder = tou_data_holder

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePageType.enable

  @property
  def text(self) -> Union[str, telebot.types.InputRichMessage]:
    return "Time of Use is disabled"

  def create_buttons(self) -> None:
    self.register_button(ButtonNode("Enable Time of Use?"))
    self.register_button(BreakButtonNode())
    self.register_button(ButtonNode("Yes"), self._handle_yes)
    self.register_button(ButtonNode("No"), self._handle_no)

  async def _handle_yes(self, navigator: TelebotPageNavigator) -> None:
    # Enable Time of Use
    self._tou_data_holder.tou_data.week.enabled = True

    # Don't write unnecessary data
    data = copy.deepcopy(self._tou_data_holder.tou_data)
    data.charges.values.clear()
    data.times.values.clear()
    data.powers.values.clear()
    data.socs.values.clear()

    try:
      await TimeOfUseHelper.write_time_of_use(
        tou_register = self._tou_register,
        tou_data = data,
      )

      tou_registers = await TimeOfUseHelper.read_time_of_use()
      tou_data = TimeOfUseHelper.get_time_of_use_data(tou_registers)
      self._tou_data_holder.actualize(tou_data)
    except Exception as e:
      await navigator.stop(TelebotUtils.escape_html(str(e)))
    else:
      await navigator.navigate(TimeOfUsePageType.main)

  async def _handle_no(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop("Time of Use is disabled")
