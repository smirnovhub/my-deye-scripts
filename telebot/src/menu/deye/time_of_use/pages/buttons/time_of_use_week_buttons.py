from button_node import ButtonNode
from time_of_use_week import TimeOfUseWeek
from break_button_node import BreakButtonNode
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TimeOfUseWeekButtons:
  def __init__(
    self,
    tou_week: TimeOfUseWeek,
  ):
    super().__init__()
    self._tou_week = tou_week

  def create_buttons(self, page: TelebotNavigationPage) -> None:
    page.register_button(ButtonNode("Mon"), self._toggle_monday)
    page.register_button(ButtonNode("Tue"), self._toggle_tuesday)
    page.register_button(ButtonNode("Wed"), self._toggle_wednesday)
    page.register_button(ButtonNode("Thu"), self._toggle_thursday)
    page.register_button(ButtonNode("Fri"), self._toggle_friday)
    page.register_button(ButtonNode("Sat"), self._toggle_saturday)
    page.register_button(ButtonNode("Sun"), self._toggle_sunday)
    page.register_button(BreakButtonNode())

    # Days of the week
    mon_btn = TimeOfUseSwitchButtonNode(enabled = self._tou_week.monday, key = "monday")
    tue_btn = TimeOfUseSwitchButtonNode(enabled = self._tou_week.tuesday, key = "tuesday")
    wed_btn = TimeOfUseSwitchButtonNode(enabled = self._tou_week.wednesday, key = "wednesday")
    thu_btn = TimeOfUseSwitchButtonNode(enabled = self._tou_week.thursday, key = "thursday")
    fri_btn = TimeOfUseSwitchButtonNode(enabled = self._tou_week.friday, key = "friday")
    sat_btn = TimeOfUseSwitchButtonNode(enabled = self._tou_week.saturday, key = "saturday")
    sun_btn = TimeOfUseSwitchButtonNode(enabled = self._tou_week.sunday, key = "sunday")

    page.register_button(mon_btn, self._toggle_monday)
    page.register_button(tue_btn, self._toggle_tuesday)
    page.register_button(wed_btn, self._toggle_wednesday)
    page.register_button(thu_btn, self._toggle_thursday)
    page.register_button(fri_btn, self._toggle_friday)
    page.register_button(sat_btn, self._toggle_saturday)
    page.register_button(sun_btn, self._toggle_sunday)
    page.register_button(BreakButtonNode())

  async def _toggle_monday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.monday = not self._tou_week.monday
    await navigator.update()

  async def _toggle_tuesday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.tuesday = not self._tou_week.tuesday
    await navigator.update()

  async def _toggle_wednesday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.wednesday = not self._tou_week.wednesday
    await navigator.update()

  async def _toggle_thursday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.thursday = not self._tou_week.thursday
    await navigator.update()

  async def _toggle_friday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.friday = not self._tou_week.friday
    await navigator.update()

  async def _toggle_saturday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.saturday = not self._tou_week.saturday
    await navigator.update()

  async def _toggle_sunday(self, navigator: TelebotPageNavigator) -> None:
    self._tou_week.sunday = not self._tou_week.sunday
    await navigator.update()
