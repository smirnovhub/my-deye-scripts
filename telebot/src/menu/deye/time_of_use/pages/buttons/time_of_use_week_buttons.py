from typing import List

from button_node import ButtonNode
from time_of_use_week import TimeOfUseWeek
from break_button_node import BreakButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TimeOfUseWeekButtons:
  def __init__(
    self,
    page: TelebotNavigationPage,
    tou_week: TimeOfUseWeek,
  ):
    super().__init__()
    self._tou_week = tou_week

    header_buttons: List[ButtonNode] = [
      page.register_button_handler(ButtonNode("Mon"), self._toggle_monday),
      page.register_button_handler(ButtonNode("Tue"), self._toggle_tuesday),
      page.register_button_handler(ButtonNode("Wed"), self._toggle_wednesday),
      page.register_button_handler(ButtonNode("Thu"), self._toggle_thursday),
      page.register_button_handler(ButtonNode("Fri"), self._toggle_friday),
      page.register_button_handler(ButtonNode("Sat"), self._toggle_saturday),
      page.register_button_handler(ButtonNode("Sun"), self._toggle_sunday),
      BreakButtonNode(),
    ]

    # Days of the week
    mon_btn = TimeOfUseSwitchButtonNode(enabled = tou_week.monday)
    tue_btn = TimeOfUseSwitchButtonNode(enabled = tou_week.tuesday)
    wed_btn = TimeOfUseSwitchButtonNode(enabled = tou_week.wednesday)
    thu_btn = TimeOfUseSwitchButtonNode(enabled = tou_week.thursday)
    fri_btn = TimeOfUseSwitchButtonNode(enabled = tou_week.friday)
    sat_btn = TimeOfUseSwitchButtonNode(enabled = tou_week.saturday)
    sun_btn = TimeOfUseSwitchButtonNode(enabled = tou_week.sunday)

    buttons = [
      page.register_button_handler(mon_btn, self._toggle_monday),
      page.register_button_handler(tue_btn, self._toggle_tuesday),
      page.register_button_handler(wed_btn, self._toggle_wednesday),
      page.register_button_handler(thu_btn, self._toggle_thursday),
      page.register_button_handler(fri_btn, self._toggle_friday),
      page.register_button_handler(sat_btn, self._toggle_saturday),
      page.register_button_handler(sun_btn, self._toggle_sunday),
      BreakButtonNode(),
    ]

    self._buttons = header_buttons + buttons

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def _toggle_monday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.monday = not self._tou_week.monday
    navigator.update()

  def _toggle_tuesday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.tuesday = not self._tou_week.tuesday
    navigator.update()

  def _toggle_wednesday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.wednesday = not self._tou_week.wednesday
    navigator.update()

  def _toggle_thursday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.thursday = not self._tou_week.thursday
    navigator.update()

  def _toggle_friday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.friday = not self._tou_week.friday
    navigator.update()

  def _toggle_saturday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.saturday = not self._tou_week.saturday
    navigator.update()

  def _toggle_sunday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.sunday = not self._tou_week.sunday
    navigator.update()
