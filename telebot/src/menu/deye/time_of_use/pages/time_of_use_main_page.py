from enum import Enum
from typing import List

from button_node import ButtonNode
from break_button_node import BreakButtonNode
from pages.time_of_use_page import TimeOfUsePage
from time_of_use_button_node import TimeOfUseButtonNode
from time_of_use_data import TimeOfUseData
from telebot_navigation_page import TelebotNavigationPage
from telebot_page_navigator import TelebotPageNavigator
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode
from time_of_use_time_button_node import TimeOfUseTimeButtonNode

class TimeOfUseMainPage(TelebotNavigationPage):
  def __init__(self, tou_data: TimeOfUseData):
    self._tou_data = tou_data
    self._save_button = ButtonNode("Save")
    self._reset_button = ButtonNode("Reset")
    self._week_button = ButtonNode("Week")
    self._cancel_button = ButtonNode("Cancel")

  @property
  def page_type(self) -> Enum:
    return TimeOfUsePage.main

  def update(self) -> None:
    header_buttons: List[ButtonNode] = [
      ButtonNode("Grid"),
      ButtonNode("Gen"),
      ButtonNode("Start"),
      ButtonNode("End"),
      ButtonNode("Pwr"),
      ButtonNode("SOC"),
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
      self._start_time_buttons.append(
        TimeOfUseTimeButtonNode(
          text = f"{time.hour:02d}:{time.minute:02d}",
          index = index,
        ))

      next_value = self._tou_data.times.values[(index + 1) % len(self._tou_data.times.values)]

      self._end_time_buttons.append(
        TimeOfUseTimeButtonNode(
          text = f"{next_value.hour:02d}:{next_value.minute:02d}",
          index = index,
        ))

    self._powers_buttons: List[ButtonNode] = []

    for index, power in enumerate(self._tou_data.powers.values):
      self._powers_buttons.append(TimeOfUseButtonNode(
        text = str(power),
        index = index,
      ))

    self._socs_buttons: List[ButtonNode] = []

    for index, soc in enumerate(self._tou_data.socs.values):
      self._socs_buttons.append(TimeOfUseButtonNode(
        text = str(soc),
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
    if button.data == self._save_button.data:
      print("SAVE click")
    elif button.data == self._reset_button.data:
      print("RESET click")
    elif button.data == self._week_button.data:
      print("WEEK click")
    elif button.data == self._cancel_button.data:
      print("CANCEL click")

    if isinstance(button, TimeOfUseSwitchButtonNode):
      button.switch()
      navigator.update()

      for btn in self._grid_charge_buttons:
        if btn.data == button.data:
          self._tou_data.charges.values[button.index].grid_charge = button.enabled
          return

      for btn in self._gen_charge_buttons:
        if btn.data == button.data:
          self._tou_data.charges.values[button.index].gen_charge = button.enabled
          return

      return

    if isinstance(button, TimeOfUseButtonNode):
      for btn in self._start_time_buttons:
        if btn.data == button.data:
          navigator.navigate(TimeOfUsePage.start_hours, time_of_use_line_index = button.index)
          return

      for btn in self._end_time_buttons:
        if btn.data == button.data:
          index = (button.index + 1) % len(self._end_time_buttons)
          navigator.navigate(TimeOfUsePage.end_hours, time_of_use_line_index = index)
          return

      for btn in self._powers_buttons:
        if btn.data == button.data:
          navigator.navigate(TimeOfUsePage.powers, time_of_use_line_index = button.index)
          return

      for btn in self._socs_buttons:
        if btn.data == button.data:
          navigator.navigate(TimeOfUsePage.socs, time_of_use_line_index = button.index)
          return

  @property
  def buttons(self) -> List[ButtonNode]:
    return self._buttons
