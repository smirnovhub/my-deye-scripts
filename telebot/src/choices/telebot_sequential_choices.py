import telebot

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass

from button_node import ButtonNode
from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants

class SimpleButtonNode(ButtonNode):
  def __init__(
    self,
    text: str,
    data: str = "",
    children: Optional[List["SimpleButtonNode"]] = None,
  ):
    super().__init__(
      text = text,
      data = data,
    )
    self.children = children if children else []

@dataclass
class StepState:
  """
  Holds the state of a sequential selection using SimpleButtonNode tree.
  """
  message_text: str
  current_node: SimpleButtonNode
  results: List[SimpleButtonNode]
  message_id: int
  max_per_row: int
  final_callback: Callable[[int, List[SimpleButtonNode]], None]

class SequentialChoices:
  _seq_prefix = "_seq_"
  _step_states: Dict[int, StepState] = {}
  _is_global_handler_registered = False

  @staticmethod
  def ask_sequential_choices(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    root: SimpleButtonNode,
    final_callback: Callable[[int, List[SimpleButtonNode]], None],
    max_per_row: int = 5,
  ) -> telebot.types.Message:
    """
    Starts a sequential menu using SimpleButtonNode tree.
    """
    if not root.children:
      return bot.send_message(chat_id, text, parse_mode = "HTML")

    SequentialChoices._register_global_handler(bot)

    keyboard = TelebotUtils.get_keyboard_for_buttons(
      buttons = root.children,
      max_per_row = max_per_row,
      data_prefix = SequentialChoices._seq_prefix,
    )

    message = bot.send_message(
      chat_id,
      text,
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
    )

    bot.clear_step_handler_by_chat_id(chat_id)
    bot.register_next_step_handler(
      message,
      SequentialChoices._text_input_handler,
      bot,
      message.message_id,
    )

    return message

  @staticmethod
  def _text_input_handler(message: telebot.types.Message, bot: telebot.TeleBot, message_id: int):
    """
    Handles plain text input after sequential buttons.
    """
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
      bot.answer_callback_query(call.id)

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

      # callback_data is index of SimpleButtonNode child
      button_id_str = call.data[len(SequentialChoices._seq_prefix):]

      try:
        button_id = int(button_id_str)
      except ValueError:
        return

      child_node: Optional[SimpleButtonNode] = None
      for child in current_node.children:
        if child.id == button_id:
          child_node = child
          break

      if child_node is None:
        raise RuntimeError(f"Child button with id {button_id} not found")

      # save the button label clicked
      state.results.append(child_node)

      if not child_node.children:
        TelebotUtils.remove_inline_buttons_with_delay(
          bot = bot,
          chat_id = chat_id,
          message_id = state.message_id,
          delay = TelebotConstants.buttons_remove_delay_sec,
        )

        state.final_callback(chat_id, state.results)
        del SequentialChoices._step_states[chat_id]
        return

      # go to child node
      state.current_node = child_node

      # Use a list comprehension to create the options for the extended keyboard
      keyboard = TelebotUtils.get_keyboard_for_buttons(
        buttons = child_node.children,
        max_per_row = state.max_per_row,
        data_prefix = SequentialChoices._seq_prefix,
      )

      # Check if message text or keyboard actually changed
      is_markup_changed = keyboard.to_dict() != call.message.reply_markup.to_dict()
      try:
        if is_markup_changed:
          bot.edit_message_reply_markup(
            chat_id = chat_id,
            message_id = state.message_id,
            reply_markup = keyboard,
          )
      except Exception:
        pass
