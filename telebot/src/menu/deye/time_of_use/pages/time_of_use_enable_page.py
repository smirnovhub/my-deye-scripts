import copy

from enum import Enum
from typing import List

from button_node import ButtonNode
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
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
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    self._buttons = [
      ButtonNode("Enable Time of Use?"),
      BreakButtonNode(),
      self.register_button_handler(ButtonNode("Yes"), self._handle_yes),
      self.register_button_handler(ButtonNode("No"), self._handle_no),
    ]

  def _handle_yes(self, navigator: TelebotPageNavigator) -> None:
    # Enable Time of Use
    self._tou_data.week.enabled = True

    # Don't write unnecessary data
    data = copy.deepcopy(self._tou_data)
    data.charges.values.clear()
    data.times.values.clear()
    data.powers.values.clear()
    data.socs.values.clear()

    try:
      TimeOfUseHelper.write_time_of_use(
        tou_register = self._tou_register,
        master_logger = self._loggers.master,
        tou_data = data,
      )
    except Exception as e:
      navigator.stop(str(e))
    else:
      navigator.navigate(TimeOfUsePage.main, "Time of Use schedule:")

  def _handle_no(self, navigator: TelebotPageNavigator) -> None:
    navigator.stop("Time of Use is disabled")
