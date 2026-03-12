from dataclasses import dataclass

from telebot_sequential_choices import ButtonNode
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

@dataclass
class TimeOfUseButtonLine:
  grid_charge_button: TimeOfUseSwitchButtonNode
  gen_charge_button: TimeOfUseSwitchButtonNode
  start_time_button: ButtonNode
  end_time_button: ButtonNode
  power_button: ButtonNode
  soc_button: ButtonNode
