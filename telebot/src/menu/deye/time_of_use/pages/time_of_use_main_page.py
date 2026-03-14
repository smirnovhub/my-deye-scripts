import copy

from dataclasses import asdict
from enum import Enum
from typing import List

from common_utils import CommonUtils
from button_node import ButtonNode
from break_button_node import BreakButtonNode
from custom_single_registers import CustomSingleRegisters
from telebot_deye_helper import TelebotDeyeHelper
from time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from time_of_use_data import TimeOfUseData
from deye_registers_holder import DeyeLoggers, DeyeRegisters, DeyeRegistersHolder
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TimeOfUseMainPage(TelebotNavigationPage):
  def __init__(self, tou_data: TimeOfUseData):
    self._tou_data = tou_data
    self._tou_original_data = copy.deepcopy(tou_data)
    self._save_button = ButtonNode("Save")
    self._reset_button = ButtonNode("Reset")
    self._week_button = ButtonNode("Week")
    self._cancel_button = ButtonNode("Cancel")
    self._loggers = DeyeLoggers()
    registers = DeyeRegisters()
    self._register = registers.time_of_use_register

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons

  def update(self) -> None:
    header_buttons: List[ButtonNode] = [
      ButtonNode("Grid"),
      ButtonNode("Gen"),
      ButtonNode("Start"),
      ButtonNode("End"),
      ButtonNode("Pwr"),
      ButtonNode("Batt"),
      BreakButtonNode(),
    ]

    bottom_buttons: List[ButtonNode] = [
      self._save_button,
      self._reset_button,
      self._week_button,
      self._cancel_button,
    ]

    self._grid_charge_buttons: List[ButtonNode] = []
    self._gen_charge_buttons: List[ButtonNode] = []

    for index, charge in enumerate(self._tou_data.charges.values):
      self._grid_charge_buttons.append(TimeOfUseSwitchButtonNode(
        enabled = charge.grid_charge,
        index = index,
      ))

      self._gen_charge_buttons.append(TimeOfUseSwitchButtonNode(
        enabled = charge.gen_charge,
        index = index,
      ))

    self._start_time_buttons: List[ButtonNode] = []
    self._end_time_buttons: List[ButtonNode] = []

    for index, time in enumerate(self._tou_data.times.values):
      self._start_time_buttons.append(TimeOfUseButtonNode(
        text = f"{time.hour:02d}:{time.minute:02d}",
        index = index,
      ))

      next_value = self._tou_data.times.values[(index + 1) % len(self._tou_data.times.values)]

      self._end_time_buttons.append(
        TimeOfUseButtonNode(
          text = f"{next_value.hour:02d}:{next_value.minute:02d}",
          index = index,
        ))

    self._powers_buttons: List[ButtonNode] = []

    for index, power in enumerate(self._tou_data.powers.values):
      self._powers_buttons.append(TimeOfUseButtonNode(
        text = str(power),
        data = str(power),
        index = index,
      ))

    self._socs_buttons: List[ButtonNode] = []

    for index, soc in enumerate(self._tou_data.socs.values):
      self._socs_buttons.append(TimeOfUseButtonNode(
        text = f"{soc}%",
        data = str(soc),
        index = index,
      ))

    self._tou_buttons: List[ButtonNode] = []

    for index, _ in enumerate(self._socs_buttons):
      self._tou_buttons.extend([
        self._grid_charge_buttons[index],
        self._gen_charge_buttons[index],
        self._start_time_buttons[index],
        self._end_time_buttons[index],
        self._powers_buttons[index],
        self._socs_buttons[index],
        BreakButtonNode(),
      ])

    self._buttons = header_buttons + self._tou_buttons + bottom_buttons

  def on_button_clicked(self, navigator: TelebotPageNavigator, button: ButtonNode) -> None:
    if button.id == self._save_button.id:
      text = self.get_time_of_use_as_text(self._tou_data)
      navigator.stop(text)
      self._clear_unchanged_data(
        data = self._tou_data,
        original_data = self._tou_original_data,
      )
      self._write_time_of_use()
    elif button.id == self._reset_button.id:
      self._reset_time_intervals()
      self.update()
      navigator.update()
      return
    elif button.id == self._week_button.id:
      print("WEEK click")
    elif button.id == self._cancel_button.id:
      text = self.get_time_of_use_as_text(self._tou_original_data)
      navigator.stop(text)
      return

    if isinstance(button, TimeOfUseSwitchButtonNode):
      button.switch()
      navigator.update()

      for btn in self._grid_charge_buttons:
        if btn.id == button.id:
          self._tou_data.charges.values[button.index].grid_charge = button.enabled
          return

      for btn in self._gen_charge_buttons:
        if btn.id == button.id:
          self._tou_data.charges.values[button.index].gen_charge = button.enabled
          return

      return

    if isinstance(button, TimeOfUseButtonNode):
      for btn in self._start_time_buttons:
        if btn.id == button.id:
          navigator.navigate(TimeOfUsePage.start_hours, time_of_use_line_index = button.index)
          return

      for btn in self._end_time_buttons:
        if btn.id == button.id:
          index = (button.index + 1) % len(self._end_time_buttons)
          navigator.navigate(TimeOfUsePage.end_hours, time_of_use_line_index = index)
          return

      for btn in self._powers_buttons:
        if btn.id == button.id:
          navigator.navigate(TimeOfUsePage.powers, time_of_use_line_index = button.index)
          return

      for btn in self._socs_buttons:
        if btn.id == button.id:
          navigator.navigate(TimeOfUsePage.socs, time_of_use_line_index = button.index)
          return

  def get_time_of_use_as_text(self, data: TimeOfUseData) -> str:
    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    weekly = data.weeks.values[0]

    header = f'{sign(weekly.enabled)} Time of Use schedule:\n'
    schedule = 'Gr Gen    Time     Pwr SOC\n'

    charges = data.charges.values
    times = data.times.values
    powers = data.powers.values
    socs = data.socs.values

    count = len(times)
    for i in range(count):
      curr_charge = charges[i]
      curr_time = times[i]
      # Next time for the interval end, wrapping around to the first element
      next_time = times[(i + 1) % count]
      curr_power = powers[i]
      curr_soc = socs[i]

      schedule += (f'{sign(curr_charge.grid_charge)} {sign(curr_charge.gen_charge)} '
                   f'{curr_time.hour:02d}:{curr_time.minute:02d} '
                   f'{next_time.hour:02d}:{next_time.minute:02d} '
                   f'{curr_power:>4} {curr_soc:>3}\n')

    days_of_week = 'Mon Tue Wed Thu Fri Sat Sun\n'
    days_of_week += (f'{sign(weekly.monday)}  '
                     f'{sign(weekly.tuesday)}  '
                     f'{sign(weekly.wednesday)}  '
                     f'{sign(weekly.thursday)}  '
                     f'{sign(weekly.friday)}  '
                     f'{sign(weekly.saturday)}  '
                     f'{sign(weekly.sunday)}')

    return f'{header}<pre>{schedule}</pre>\n<pre>{days_of_week}</pre>'

  def _write_time_of_use(self) -> None:
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self._loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(self._register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    if asdict(self._tou_data) == asdict(self._tou_original_data):
      print("NO")
      return

    try:
      holder.write_register(self._register, self._tou_data)
    finally:
      holder.disconnect()

  def _reset_time_intervals(self) -> None:
    """
    Directly updates the hour and minute attributes of existing TimeOfUseTime objects.
    """
    values = self._tou_data.times.values

    total_intervals = len(values)
    if total_intervals == 0:
      return

    hours_per_step = 24 // total_intervals

    # Update only existing objects in the list
    for i in range(min(total_intervals, len(values))):
      curr_time = values[i]

      # Modify attributes in-place
      curr_time.hour = i * hours_per_step
      curr_time.minute = 0

  def _clear_unchanged_data(
    self,
    data: TimeOfUseData,
    original_data: TimeOfUseData,
  ):
    # Convert parts to dicts for simple comparison
    # Use asdict to compare the entire content, not object references
    if asdict(data.charges) == asdict(original_data.charges):
      data.charges.values = []

    if asdict(data.times) == asdict(original_data.times):
      data.times.values = []

    if asdict(data.powers) == asdict(original_data.powers):
      data.powers.values = []

    if asdict(data.socs) == asdict(original_data.socs):
      data.socs.values = []

    if asdict(data.weeks) == asdict(original_data.weeks):
      data.weeks.values = []
