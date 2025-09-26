# mypy: ignore-errors
import telebot

from typing import Dict, List, Callable
from telebot_user_choices_helper import get_keyboard_for_choices
from telebot_utils import remove_inline_buttons_with_delay
from telebot_constants import buttons_remove_delay_sec

# Private constants for state dictionary keys (lowercase)
_current_step_str = "current_step"
_message_text_str = "message_text"
_options_array_str = "options_array"
_results_str = "results"
_message_id_str = "message_id"
_max_per_row_str = "max_per_row"
_final_callback_str = "final_callback"
_user_input_callback_str = "user_input_callback"

# Prefix for sequential choice buttons
_sequential_prefix_str = "_seq_"

# Storage for sequential step states: chat_id -> state
_step_states = {}

# Flag to ensure we register the global callback handler only once per bot instance
_is_global_handler_registered = False

def ask_sequential_choices(
  bot: telebot.TeleBot,
  chat_id: int,
  text: str,
  options_array: List[Dict[str, str]],
  final_callback: Callable[[int, List[str]], None],
  user_input_callback: Callable[[int, str], None],
  max_per_row: int = 5,
) -> telebot.types.Message:
  """
  Sends a message with inline keyboards for multiple sequential choices.
  Uses a single global callback handler for all steps (safe for multiple invocations).

  Parameters:
      bot: TeleBot instance.
      chat_id: Telegram chat ID.
      text: Text of the initial message.
      options_array: List of dicts; each dict is a step with button_label -> callback_data.
      final_callback: Function(chat_id, results_list) called at the end.
      max_per_row: Maximum buttons per row.

  Returns:
      telebot.types.Message: The message object sent.
  """
  if not options_array:
    return bot.send_message(chat_id, text, parse_mode = "HTML")

  _register_global_handler(bot)

  # Initialize state for this chat
  _step_states[chat_id] = {
    _message_text_str: text,
    _options_array_str: options_array,
    _results_str: [],
    _current_step_str: 0,
    _message_id_str: None,
    _max_per_row_str: max_per_row,
    _final_callback_str: final_callback,
    _user_input_callback_str: user_input_callback,
  }

  # Send initial message with first step buttons
  first_step_options = options_array[0]
  keyboard = get_keyboard_for_choices(first_step_options, max_per_row, _sequential_prefix_str)
  message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = "HTML")
  _step_states[chat_id][_message_id_str] = message.message_id

  # Clear any pending next-step handlers for this chat
  bot.clear_step_handler_by_chat_id(message.chat.id)
  bot.register_next_step_handler(
    message,
    _sequential_choices_next_step_handler,
    bot,
    message.message_id,
  )

  return message

def _sequential_choices_next_step_handler(
  message: telebot.types.Message,
  bot: telebot.TeleBot,
  message_id: int,
):
  """
  Handles user input after a choice message is sent.
  - Removes the inline keyboard from the original message.
  - If input is a command, passes it to normal command handling.
  - If input matches one of the valid options, calls the stored callback.
  - Otherwise, replies with a warning message if provided.
  """
  remove_inline_buttons_with_delay(
    bot = bot,
    chat_id = message.chat.id,
    message_id = message_id,
    delay = buttons_remove_delay_sec,
  )

  # if we received new command, process it
  if message.text.startswith('/'):
    bot.process_new_messages([message])
    return

  # Call the optional text callback with user's input
  state = _step_states.get(message.chat.id)
  if state and state.get(_user_input_callback_str):
    state[_user_input_callback_str](message.chat.id, message.text)

def _register_global_handler(bot: telebot.TeleBot):
  """
  Register a single global callback handler for sequential choice steps.
  Only triggers for buttons defined in the current step of an active chat.
  """
  global _is_global_handler_registered
  if _is_global_handler_registered:
    return

  _is_global_handler_registered = True

  @bot.callback_query_handler(func = lambda c: _is_valid_sequential_choice(bot, c))
  def handle_sequential_choice(call: telebot.types.CallbackQuery):
    chat_id = call.message.chat.id
    state = _step_states.get(chat_id)

    # If bot restarted and no state exists, remove buttons
    if not state:
      remove_inline_buttons_with_delay(
        bot = bot,
        chat_id = chat_id,
        message_id = call.message.message_id,
        delay = buttons_remove_delay_sec,
      )

      # No active sequential step for this chat
      return

    options_array = state[_options_array_str]
    message_id = state[_message_id_str]
    max_per_row = state[_max_per_row_str]

    # Save the choice (without prefix)
    clean_data = call.data[len(_sequential_prefix_str):]
    state[_results_str].append(clean_data)
    state[_current_step_str] += 1

    bot.answer_callback_query(call.id)

    # If last step, call final callback
    if state[_current_step_str] >= len(options_array):
      remove_inline_buttons_with_delay(
        bot = bot,
        chat_id = chat_id,
        message_id = message_id,
        delay = buttons_remove_delay_sec,
      )
      state[_final_callback_str](chat_id, state[_results_str])
      del _step_states[chat_id]
      return

    # Otherwise, send next step buttons
    next_options = options_array[state[_current_step_str]]
    keyboard = get_keyboard_for_choices(next_options, max_per_row, _sequential_prefix_str)
    bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = keyboard)

def _is_valid_sequential_choice(bot: telebot.TeleBot, call: telebot.types.CallbackQuery) -> bool:
  """
  Check if the callback belongs to an active sequential choice step.
  """
  if not call.data.startswith(_sequential_prefix_str):
    return False

  chat_id = call.message.chat.id
  state = _step_states.get(chat_id)

  # If no state exists (bot restarted), remove buttons
  if not state:
    remove_inline_buttons_with_delay(
      bot = bot,
      chat_id = chat_id,
      message_id = call.message.message_id,
      delay = buttons_remove_delay_sec,
    )
    return False

  step_idx = state[_current_step_str]
  options_array = state[_options_array_str]
  if step_idx >= len(options_array):
    return False

  clean_data = call.data[len(_sequential_prefix_str):]
  return clean_data in options_array[step_idx].values()
