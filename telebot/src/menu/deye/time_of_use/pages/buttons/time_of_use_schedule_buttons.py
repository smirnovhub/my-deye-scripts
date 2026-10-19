from enum import Enum

from button_node import ButtonNode
from button_style import ButtonStyle
from time_of_use_data import TimeOfUseData
from time_of_use_page import TimeOfUsePage
from break_button_node import BreakButtonNode
from time_of_use_times import TimeOfUseTimes
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TimeOfUseScheduleButtons:
  def __init__(
    self,
    tou_data: TimeOfUseData,
  ):
    super().__init__()
    self._tou_data = tou_data
    self._is_data_correct = True

  def create_buttons(self, page: TelebotNavigationPage) -> None:
    page.register_button(ButtonNode("Grid"), self._toggle_all_grid)
    page.register_button(ButtonNode("Gen"), self._toggle_all_gen)
    page.register_button(ButtonNode("Start"), self._handle_nothing)
    page.register_button(ButtonNode("End"), self._handle_nothing)
    page.register_button(ButtonNode("Pwr"), self._create_navigation_handler(TimeOfUsePage.powers))
    page.register_button(ButtonNode("Batt"), self._create_navigation_handler(TimeOfUsePage.socs))
    page.register_button(BreakButtonNode())

    charges = self._tou_data.charges.values
    times = self._tou_data.times.values
    powers = self._tou_data.powers.values
    socs = self._tou_data.socs.values

    count = len(times)

    for i in range(count):
      charge = charges[i]
      time = times[i]
      next_time = times[(i + 1) % count]

      style = ButtonStyle.default
      if not TimeOfUseTimes.is_interval_correct(start = time, end = next_time):
        self._is_data_correct = False
        style = ButtonStyle.danger

      grid = TimeOfUseSwitchButtonNode(enabled = charge.grid_charge, key = f"grid{i}")
      gen = TimeOfUseSwitchButtonNode(enabled = charge.gen_charge, key = f"gen{i}")
      start = ButtonNode(text = f"{time.hour:02d}:{time.minute:02d}", style = style, key = f"start{i}")
      end = ButtonNode(text = f"{next_time.hour:02d}:{next_time.minute:02d}", style = style, key = f"end{i}")
      power = ButtonNode(text = str(powers[i]), key = f"power{i}")
      soc = ButtonNode(text = f"{socs[i]}%", key = f"soc{i}")

      page.register_button(grid, self._create_toggle_grid_handler(i))
      page.register_button(gen, self._create_toggle_gen_handler(i))
      page.register_button(start, self._create_navigation_handler(TimeOfUsePage.start_hours, i))
      page.register_button(end, self._create_navigation_handler(TimeOfUsePage.end_hours, (i + 1) % count))
      page.register_button(power, self._create_navigation_handler(TimeOfUsePage.powers, i))
      page.register_button(soc, self._create_navigation_handler(TimeOfUsePage.socs, i))
      page.register_button(BreakButtonNode())

  @property
  def is_data_correct(self) -> bool:
    return self._is_data_correct

  def _create_toggle_grid_handler(self, line_index: int):
    # The handler now accepts both navigator and button_node
    async def handler(navigator: TelebotPageNavigator) -> None:
      value = self._tou_data.charges.values[line_index].grid_charge
      self._tou_data.charges.values[line_index].grid_charge = not value
      await navigator.update()

    return handler

  async def _toggle_all_grid(self, navigator: TelebotPageNavigator):
    # Determine target state: if any is disabled, enable all. Otherwise, disable all.
    charges = self._tou_data.charges.values
    target_state = any(not c.grid_charge for c in charges)

    for charge in charges:
      charge.grid_charge = target_state

    await navigator.update()

  def _create_toggle_gen_handler(self, line_index: int):
    # The handler now accepts both navigator and button_node
    async def handler(navigator: TelebotPageNavigator) -> None:
      value = self._tou_data.charges.values[line_index].gen_charge
      self._tou_data.charges.values[line_index].gen_charge = not value
      await navigator.update()

    return handler

  async def _toggle_all_gen(self, navigator: TelebotPageNavigator):
    # Determine target state: if any is disabled, enable all. Otherwise, disable all.
    charges = self._tou_data.charges.values
    target_state = any(not c.gen_charge for c in charges)

    for charge in charges:
      charge.gen_charge = target_state

    await navigator.update()

  def _create_navigation_handler(self, target_page: Enum, line_index: int = -1):
    async def handler(navigator: TelebotPageNavigator) -> None:
      await navigator.navigate(target_page, time_of_use_line_index = line_index)

    return handler

  async def _handle_nothing(self, navigator: TelebotPageNavigator) -> None:
    await navigator.send_message_with_remove_with_delay(
      text = "This button does nothing",
      delay = 1,
    )
