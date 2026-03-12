import random
import telebot

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass

from telebot_user_choice import TelebotUserChoice
from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants

class ButtonNode:
  def __init__(
    self,
    label: str,
    text: str = '',
    children: Optional[List["ButtonNode"]] = None,
  ):
    self.label: str = label
    self.text: str = text
    # Use a list if provided, otherwise create a new empty list
    self.children: List["ButtonNode"] = children if children is not None else []

  def set_label(self, label: str) -> None:
    self.label = label

  def __repr__(self) -> str:
    # Added repr for easier debugging, similar to what dataclass provides
    return f"ButtonNode(label={self.label!r}, text={self.text!r}, children_count={len(self.children)})"

@dataclass
class StepState:
  """
  Holds the state of a sequential selection using ButtonNode tree.
  """
  message_text: str
  current_node: ButtonNode
  results: List[ButtonNode]
  message_id: int
  max_per_row: int
  final_callback: Optional[Callable[[int, List[ButtonNode]], None]] = None
  step_callback: Optional[Callable[[int, ButtonNode], None]] = None

class SequentialChoices:
  _seq_prefix = "_seq_"
  _step_states: Dict[int, StepState] = {}
  _is_global_handler_registered = False

  @staticmethod
  def ask_sequential_choices(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    root: ButtonNode,
    final_callback: Optional[Callable[[int, List[ButtonNode]], None]] = None,
    step_callback: Optional[Callable[[int, ButtonNode], None]] = None,
    text_if_next_command_received: Optional[Callable[[], str]] = None,
    max_per_row: int = 5,
  ) -> telebot.types.Message:
    """
    Starts a sequential menu using ButtonNode tree.
    """
    if not root.children:
      return bot.send_message(chat_id, text, parse_mode = "HTML")

    SequentialChoices._register_global_handler(bot)

    choices = [TelebotUserChoice(
      text = child.label,
      data = str(i),
    ) for i, child in enumerate(root.children)]

    keyboard = TelebotUtils.get_keyboard_for_choices_ext(
      options = choices,
      max_per_row = max_per_row,
      data_prefix = SequentialChoices._seq_prefix,
    )

    message = bot.send_message(
      chat_id,
      root.text if root.text else text,
      reply_markup = keyboard,
      parse_mode = "HTML",
    )

    SequentialChoices._step_states[chat_id] = StepState(
      message_text = text,
      current_node = root,
      results = [],
      message_id = message.message_id,
      max_per_row = max_per_row,
      final_callback = final_callback,
      step_callback = step_callback,
    )

    bot.clear_step_handler_by_chat_id(chat_id)
    bot.register_next_step_handler(
      message,
      SequentialChoices._text_input_handler,
      bot,
      message.message_id,
      text_if_next_command_received,
    )

    return message

  @staticmethod
  def _text_input_handler(
    message: telebot.types.Message,
    bot: telebot.TeleBot,
    message_id: int,
    text_if_next_command_received: Optional[Callable[[], str]],
  ):
    """
    Handles plain text input after sequential buttons.
    """
    if text_if_next_command_received:
      try:
        bot.edit_message_text(
          text_if_next_command_received(),
          chat_id = message.chat.id,
          message_id = message_id,
          reply_markup = None,
          parse_mode = 'HTML',
        )
      except Exception:
        pass
    else:
      TelebotUtils.remove_inline_buttons_with_delay(
        bot = bot,
        chat_id = message.chat.id,
        message_id = message_id,
        delay = TelebotConstants.buttons_remove_delay_sec,
      )

    if TelebotUtils.forward_next(bot, message):
      return

  @staticmethod
  def _register_global_handler(bot: telebot.TeleBot):
    if SequentialChoices._is_global_handler_registered:
      return
    SequentialChoices._is_global_handler_registered = True

    @bot.callback_query_handler(func = TelebotUtils.make_callback_query_filter(SequentialChoices._seq_prefix))
    def _handler(call: telebot.types.CallbackQuery):
      chat_id = call.message.chat.id
      state = SequentialChoices._step_states.get(chat_id)
      if not state:
        TelebotUtils.remove_inline_buttons_with_delay(
          bot = bot,
          chat_id = chat_id,
          message_id = call.message.message_id,
          delay = TelebotConstants.buttons_remove_delay_sec,
        )
        return

      current_node = state.current_node

      # callback_data is index of ButtonNode child
      index_str = call.data[len(SequentialChoices._seq_prefix):]
      try:
        index = int(index_str)
      except ValueError:
        return

      if index < 0 or index >= len(current_node.children):
        return

      child_node = current_node.children[index]
      bot.answer_callback_query(call.id)

      # Call the per-step callback if it exists
      if state.step_callback:
        state.step_callback(chat_id, child_node)

      # save the button label clicked
      state.results.append(child_node)

      if not child_node.children:
        is_text_changed = child_node.text and child_node.text != current_node.text

        if is_text_changed:
          bot.edit_message_text(
            child_node.text,
            chat_id = chat_id,
            message_id = state.message_id,
            reply_markup = None,
            parse_mode = 'HTML',
          )
        else:
          TelebotUtils.remove_inline_buttons_with_delay(
            bot = bot,
            chat_id = chat_id,
            message_id = state.message_id,
            delay = TelebotConstants.buttons_remove_delay_sec,
          )

        if state.final_callback:
          state.final_callback(chat_id, state.results)
          del SequentialChoices._step_states[chat_id]
          return

      # go to child node
      state.current_node = child_node

      def get_button_choice(index: int, label: str) -> TelebotUserChoice:
        """
        Determines the choice object for a button node.
        Returns a choice with a random text key for separators,
        otherwise (label, index_string).
        """
        if label == TelebotUtils.row_break_str:
          # Generate a unique text key for the separator to avoid collisions
          random_key: str = str(random.randint(100000, 999999))
          return TelebotUserChoice(text = random_key, data = TelebotUtils.row_break_str)

        return TelebotUserChoice(text = label, data = str(index))

      # Use a list comprehension to create the options for the extended keyboard
      keyboard = TelebotUtils.get_keyboard_for_choices_ext(
        options = [get_button_choice(i, b.label) for i, b in enumerate(child_node.children)],
        max_per_row = state.max_per_row,
        data_prefix = SequentialChoices._seq_prefix,
      )

      # Check if message text or keyboard actually changed
      is_text_changed = child_node.text and child_node.text != current_node.text
      is_markup_changed = keyboard.to_dict() != call.message.reply_markup.to_dict()

      try:
        if is_text_changed:
          bot.edit_message_text(
            child_node.text,
            chat_id = chat_id,
            message_id = state.message_id,
            reply_markup = keyboard,
            parse_mode = 'HTML',
          )
        elif is_markup_changed:
          bot.edit_message_reply_markup(
            chat_id = chat_id,
            message_id = state.message_id,
            reply_markup = keyboard,
          )
      except Exception:
        pass
