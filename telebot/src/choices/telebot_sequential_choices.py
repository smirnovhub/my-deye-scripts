import telebot

from typing import Callable, Dict, List
from dataclasses import dataclass, field

from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants

@dataclass
class ButtonNode:
  label: str
  text: str = ''
  id: str = ''
  children: List["ButtonNode"] = field(default_factory = list)

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
  final_callback: Callable[[int, List[ButtonNode]], None]

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
    final_callback: Callable[[int, List[ButtonNode]], None],
    max_per_row: int = 5,
  ) -> telebot.types.Message:
    """
    Starts a sequential menu using ButtonNode tree.
    """
    if not root.children:
      return bot.send_message(chat_id, text, parse_mode = "HTML")

    SequentialChoices._register_global_handler(bot)

    keyboard = TelebotUtils.get_keyboard_for_choices({
      child.label: str(i)
      for i, child in enumerate(root.children)
    }, max_per_row, SequentialChoices._seq_prefix)

    message = bot.send_message(chat_id, root.text if root.text else text, reply_markup = keyboard, parse_mode = "HTML")

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

      # save the button label clicked
      state.results.append(child_node)

      if not child_node.children:
        # Leaf node → finish
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
      keyboard = TelebotUtils.get_keyboard_for_choices({
        b.label: str(i)
        for i, b in enumerate(child_node.children)
      }, state.max_per_row, SequentialChoices._seq_prefix)

      try:
        if child_node.text and child_node.text != current_node.text:
          bot.edit_message_text(
            child_node.text,
            chat_id = chat_id,
            message_id = state.message_id,
            reply_markup = keyboard,
          )
        else:
          bot.edit_message_reply_markup(
            chat_id = chat_id,
            message_id = state.message_id,
            reply_markup = keyboard,
          )
      except Exception as e:
        bot.send_message(chat_id, str(e))
