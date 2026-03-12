import telebot

from typing import List, Set

from telebot_deye_helper import TelebotDeyeHelper
from telebot_sequential_choices import ButtonNode, SequentialChoices
from telebot_utils import TelebotUtils
from time_of_use_button_line import TimeOfUseButtonLine
from time_of_use_button_node import TimeOfUseButtonNode
from time_of_use_button_type import TimeOfUseButtonType
from time_of_use_data import TimeOfUseData
from custom_single_registers import CustomSingleRegisters
from telebot_menu_item import TelebotMenuItem
from deye_registers_holder import DeyeRegistersHolder
from deye_registers import DeyeRegisters
from telebot_menu_item_handler import TelebotMenuItemHandler
from time_of_use_switch_button_node import TimeOfUseSwitchButtonNode

class TelebotMenuTimeOfUseNew(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.registers = DeyeRegisters()
    self.register = self.registers.time_of_use_register
    self._message = "Time of Use schedule:"
    self._save_button_title = "Save"
    self._reset_button_title = "Reset times"
    self._cancel_button_title = "Cancel"

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_time_of_use

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(self.register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    data = self.register.value

    if not isinstance(data, TimeOfUseData):
      self.bot.send_message(
        message.chat.id,
        f'Register type is not {TimeOfUseData.__name__}',
        parse_mode = 'HTML',
      )
      return

    self.button_lines: List[TimeOfUseButtonLine] = []

    for i in range(6):
      line = TimeOfUseButtonLine(
        grid_charge_button = TimeOfUseSwitchButtonNode(enabled = False, time_of_use_index = i),
        gen_charge_button = TimeOfUseSwitchButtonNode(enabled = True, time_of_use_index = i),
        start_time_button = TimeOfUseButtonNode(
          "00:00",
          button_type = TimeOfUseButtonType.start_time,
          time_of_use_index = i,
        ),
        end_time_button = TimeOfUseButtonNode(
          "05:10",
          button_type = TimeOfUseButtonType.end_time,
          time_of_use_index = i,
        ),
        power_button = TimeOfUseButtonNode(
          "6000",
          button_type = TimeOfUseButtonType.power,
          time_of_use_index = i,
        ),
        soc_button = TimeOfUseButtonNode(
          "100",
          button_type = TimeOfUseButtonType.soc,
          time_of_use_index = i,
        ),
      )

      start_minutes = self.get_minute_buttons(
        index = i,
        button_type = TimeOfUseButtonType.start_minute,
      )

      start_hours = self.get_hour_buttons(
        index = i,
        button_type = TimeOfUseButtonType.start_hour,
        children = start_minutes,
      )

      line.start_time_button.children = start_hours

      end_minutes = self.get_minute_buttons(
        index = i,
        button_type = TimeOfUseButtonType.end_minute,
      )

      end_hours = self.get_hour_buttons(
        index = i,
        button_type = TimeOfUseButtonType.end_hour,
        children = end_minutes,
      )

      line.end_time_button.children = end_hours

      power_buttons = self.get_power_buttons(index = i)
      line.power_button.children = power_buttons

      soc_buttons = self.get_soc_buttons(index = i)
      line.soc_button.children = soc_buttons

      self.button_lines.append(line)

    all_lines_buttons = [
      button for line in self.button_lines for button in [
        line.grid_charge_button,
        line.gen_charge_button,
        line.start_time_button,
        line.end_time_button,
        line.power_button,
        line.soc_button,
      ]
    ]

    header_buttons: List[ButtonNode] = [
      self.get_back_button("Grid"),
      self.get_back_button("Gen"),
      self.get_back_button("Start"),
      self.get_back_button("End"),
      self.get_back_button("Pwr"),
      self.get_back_button("SOC"),
    ]

    bottom_buttons: List[ButtonNode] = [
      ButtonNode(
        self._save_button_title,
        text = f"{self._message} saved",
      ),
      TimeOfUseButtonNode(
        self._reset_button_title,
        button_type = TimeOfUseButtonType.reset,
        time_of_use_index = -1,
      ),
      ButtonNode(
        self._cancel_button_title,
        text = f"{self._message} nothing changed",
      ),
    ]

    all_buttons = header_buttons + all_lines_buttons + bottom_buttons

    # Root node
    root_buttons = ButtonNode(
      label = "root",
      children = all_buttons,
    )

    self.set_next_buttons_recursive(root_buttons, all_buttons)

    SequentialChoices.ask_sequential_choices(
      bot = self.bot,
      chat_id = message.chat.id,
      text = self._message,
      root = root_buttons,
      final_callback = self.on_all_choices_done,
      step_callback = self.on_button_pressed,
      max_per_row = 6,
    )

  def on_button_pressed(self, chat_id, button: ButtonNode):
    if button.label == self._reset_button_title:
      self.reset_time_intervals()
      return

    if button.label == self._save_button_title:
      print("SAVE!!!!!!")
      return

    if not isinstance(button, TimeOfUseButtonNode):
      return

    def update_time(target_node: ButtonNode, new_val: str, is_hour: bool) -> None:
      old_hour, old_minute = target_node.label.split(':', 1)
      if is_hour:
        target_node.set_label(f"{new_val}:{old_minute}")
      else:
        target_node.set_label(f"{old_hour}:{new_val}")

    def get_prev_line(index: int) -> TimeOfUseButtonLine:
      idx = (index - 1) % len(self.button_lines)
      return self.button_lines[idx]

    def get_next_line(index: int) -> TimeOfUseButtonLine:
      idx = (index + 1) % len(self.button_lines)
      return self.button_lines[idx]

    line = self.button_lines[button.time_of_use_index]

    if button.button_type == TimeOfUseButtonType.start_hour:
      prev_line = get_prev_line(button.time_of_use_index)
      update_time(line.start_time_button, button.label, True)
      update_time(prev_line.end_time_button, button.label, True)
    elif button.button_type == TimeOfUseButtonType.start_minute:
      prev_line = get_prev_line(button.time_of_use_index)
      update_time(line.start_time_button, button.label, False)
      update_time(prev_line.end_time_button, button.label, False)
    elif button.button_type == TimeOfUseButtonType.end_hour:
      next_line = get_next_line(button.time_of_use_index)
      update_time(line.end_time_button, button.label, True)
      update_time(next_line.start_time_button, button.label, True)
    elif button.button_type == TimeOfUseButtonType.end_minute:
      next_line = get_next_line(button.time_of_use_index)
      update_time(line.end_time_button, button.label, False)
      update_time(next_line.start_time_button, button.label, False)
    elif button.button_type == TimeOfUseButtonType.power_watt:
      line.power_button.set_label(button.label)
    elif button.button_type == TimeOfUseButtonType.soc_percent:
      line.soc_button.set_label(button.label)

    if isinstance(button, TimeOfUseSwitchButtonNode):
      button.set_enabled(not button.is_enabled)

  def on_all_choices_done(self, chat_id, results: List[ButtonNode]):
    pass

  def get_hour_buttons(
    self,
    index: int,
    button_type: TimeOfUseButtonType,
    children: List[ButtonNode],
  ) -> List[ButtonNode]:
    if button_type == TimeOfUseButtonType.start_hour:
      button = ButtonNode("Start hour:")
    elif button_type == TimeOfUseButtonType.end_hour:
      button = ButtonNode("End hour:")

    result: List[ButtonNode] = [button]
    result.append(ButtonNode(TelebotUtils.row_break_str))

    result.extend([
      TimeOfUseButtonNode(
        f"{i:02}",
        time_of_use_index = index,
        button_type = button_type,
        children = children,
      ) for i in range(24)
    ])

    result.append(ButtonNode(label = TelebotUtils.row_break_str))
    result.append(self.get_back_button("Back"))

    button.children = result

    return result

  def get_minute_buttons(
    self,
    index: int,
    button_type: TimeOfUseButtonType,
  ) -> List[ButtonNode]:
    if button_type == TimeOfUseButtonType.start_minute:
      button = ButtonNode("Start minute:")
    elif button_type == TimeOfUseButtonType.end_minute:
      button = ButtonNode("End minute:")

    result: List[ButtonNode] = [button]
    result.append(ButtonNode(TelebotUtils.row_break_str))

    result.extend(
      [TimeOfUseButtonNode(
        f"{i:02}",
        time_of_use_index = index,
        button_type = button_type,
      ) for i in range(0, 60, 5)])

    result.append(ButtonNode(label = TelebotUtils.row_break_str))
    result.append(self.get_back_button("Back"))

    button.children = result

    return result

  def get_power_buttons(
    self,
    index: int,
  ) -> List[ButtonNode]:
    values = [
      ['0', '250', '500'],
      ['1000', '1500', '2000'],
      ['2500', '3000', '3500'],
      ['4000', '5000', '6000'],
    ]

    button = ButtonNode("Battery power:")

    result: List[ButtonNode] = [button]
    result.append(ButtonNode(TelebotUtils.row_break_str))

    for i, row in enumerate(values):
      # Add a row break before every row except the first one
      if i > 0:
        result.append(ButtonNode(label = TelebotUtils.row_break_str))

      for power in row:
        result.append(
          TimeOfUseButtonNode(
            label = str(power),
            time_of_use_index = index,
            button_type = TimeOfUseButtonType.power_watt,
          ))

    result.append(ButtonNode(label = TelebotUtils.row_break_str))
    result.append(self.get_back_button("Back"))

    button.children = result

    return result

  def get_soc_buttons(
    self,
    index: int,
  ) -> List[ButtonNode]:
    values = [
      ['15', '20', '25', '30', '35'],
      ['40', '45', '50', '55', '60'],
      ['65', '70', '75', '80', '85'],
      ['90', '93', '95', '97', '100'],
    ]

    button = ButtonNode("Battery SOC:")

    result: List[ButtonNode] = [button]
    result.append(ButtonNode(TelebotUtils.row_break_str))

    for i, row in enumerate(values):
      # Add a row break before every row except the first one
      if i > 0:
        result.append(ButtonNode(label = TelebotUtils.row_break_str))

      for power in row:
        result.append(
          TimeOfUseButtonNode(
            label = str(power),
            time_of_use_index = index,
            button_type = TimeOfUseButtonType.soc_percent,
          ))

    result.append(ButtonNode(label = TelebotUtils.row_break_str))
    result.append(self.get_back_button("Back"))

    return result

  def get_back_button(self, label: str) -> ButtonNode:
    return TimeOfUseButtonNode(
      label,
      button_type = TimeOfUseButtonType.back,
      time_of_use_index = -1,
    )

  def set_next_buttons_recursive(
      self,
      button: ButtonNode,
      children: List[ButtonNode],
      processed: Set[ButtonNode] = set(),
  ) -> None:
    if button in processed:
      return

    processed.add(button)

    for child in button.children:
      self.set_next_buttons_recursive(child, children, processed)

    if not isinstance(button, TimeOfUseButtonNode):
      return

    types = [
      TimeOfUseButtonType.back,
      TimeOfUseButtonType.reset,
      TimeOfUseButtonType.switch,
      TimeOfUseButtonType.start_minute,
      TimeOfUseButtonType.end_minute,
      TimeOfUseButtonType.power_watt,
      TimeOfUseButtonType.soc_percent,
    ]

    if button.button_type in types:
      button.children = children

  def reset_time_intervals(self) -> None:
    """
    Divides 24 hours into 6 intervals and sets start/end times for each line.
    """
    total_intervals = len(self.button_lines) # Should be 6 based on your description
    if total_intervals == 0:
      return

    # 4 hours per interval
    hours_per_step = 24 // total_intervals

    def format_time(hours: int) -> str:
      # Ensures format like 04:00, 08:00, etc.
      return f"{hours:02d}:00"

    for i, line in enumerate(self.button_lines):
      start_hour = i * hours_per_step
      end_hour = (i + 1) * hours_per_step

      # Handle the last interval wrap-around if needed (24:00 becomes 00:00)
      # Though usually for intervals it stays 24:00 or resets to 00:00
      if end_hour == 24:
        end_hour = 0

      start_str = format_time(start_hour)
      end_str = format_time(end_hour)

      # Set labels for the buttons
      line.start_time_button.set_label(start_str)
      line.end_time_button.set_label(end_str)
