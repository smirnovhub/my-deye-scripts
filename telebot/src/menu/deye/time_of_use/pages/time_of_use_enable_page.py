import copy
import telebot

from enum import Enum
from typing import Union

from button_node import ButtonNode
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from telebot_utils import TelebotUtils
from time_of_use_data import TimeOfUseData
from break_button_node import BreakButtonNode
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page import TimeOfUsePage
from telebot_page_navigator import TelebotPageNavigator
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseEnablePage(TelebotNavigationPage):
  def __init__(
    self,
    tou_register: DeyeRegister,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._tou_register = tou_register
    self._tou_data = tou_data
    self._loggers = DeyeLoggers()

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.enable

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
    self._tou_data.week.enabled = True

    # Don't write unnecessary data
    data = copy.deepcopy(self._tou_data)
    data.charges.values.clear()
    data.times.values.clear()
    data.powers.values.clear()
    data.socs.values.clear()

    try:
      await TimeOfUseHelper.write_time_of_use(
        tou_register = self._tou_register,
        master_logger = self._loggers.master,
        tou_data = data,
      )
    except Exception as e:
      await navigator.stop(TelebotUtils.escape_html(str(e)))
    else:
      await navigator.navigate(TimeOfUsePage.main)

  async def _handle_no(self, navigator: TelebotPageNavigator) -> None:
    await navigator.stop("Time of Use is disabled")
