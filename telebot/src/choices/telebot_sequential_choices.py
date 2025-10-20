import telebot

from typing import Dict, List, Callable
from dataclasses import dataclass

from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants

@dataclass
class StepState:
  message_text: str
  options: List[Dict[str, str]]
  results: List[str]
  current_step: int
  message_id: int
  max_per_row: int
  final_callback: Callable[[int, List[str]], None]
  user_input_callback: Callable[[int, str], None]

class SequentialChoices:
  # Prefix for sequential choice buttons
  _seq_prefix = "_seq_"

  # Storage for sequential step states: chat_id -> state
  _step_states: Dict[int, StepState] = {}

  # Flag to ensure we register the global callback handler only once per bot instance
  _is_global_handler_registered = False

  @staticmethod
  def ask_sequential_choices(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    options: List[Dict[str, str]],
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
        options: List of dicts; each dict is a step with button_label -> callback_data.
        final_callback: Function(chat_id, results_list) called at the end.
        max_per_row: Maximum buttons per row.

    Returns:
        telebot.types.Message: The message object sent.
    """
    if not options:
      return bot.send_message(chat_id, text, parse_mode = "HTML")

    SequentialChoices._register_global_handler(bot)

    # Send initial message with first step buttons
    first_step_options = options[0]

    keyboard = TelebotUtils.get_keyboard_for_choices(
      first_step_options,
      max_per_row,
      SequentialChoices._seq_prefix,
    )

    message = bot.send_message(
      chat_id,
      text,
      reply_markup = keyboard,
      parse_mode = "HTML",
    )

    # Initialize state for this chat
    SequentialChoices._step_states[chat_id] = StepState(
      message_text = text,
      options = options,
      results = [],
      current_step = 0,
      message_id = message.message_id,
      max_per_row = max_per_row,
      final_callback = final_callback,
      user_input_callback = user_input_callback,
    )

    # Clear any pending next-step handlers for this chat
    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.register_next_step_handler(
      message,
      SequentialChoices._sequential_choices_next_step_handler,
      bot,
      message.message_id,
    )

    return message

  @staticmethod
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
    TelebotUtils.remove_inline_buttons_with_delay(
      bot = bot,
      chat_id = message.chat.id,
      message_id = message_id,
      delay = TelebotConstants.buttons_remove_delay_sec,
    )

    # if we received new command, process it
    if message.text.startswith('/'):
      bot.process_new_messages([message])
      return

    # Call the optional text callback with user's input
    state = SequentialChoices._step_states.get(message.chat.id)
    if state and message.text is not None:
      state.user_input_callback(message.chat.id, message.text)

  @staticmethod
  def _register_global_handler(bot: telebot.TeleBot):
    """
    Register a single global callback handler for sequential choice steps.
    Only triggers for buttons defined in the current step of an active chat.
    """
    if SequentialChoices._is_global_handler_registered:
      return

    SequentialChoices._is_global_handler_registered = True

    @bot.callback_query_handler(func = TelebotUtils.make_callback_query_filter(SequentialChoices._seq_prefix))
    def handle_sequential_choice(call: telebot.types.CallbackQuery):
      chat_id = call.message.chat.id
      state = SequentialChoices._step_states.get(chat_id)

      # If bot restarted and no state exists, remove buttons
      if not state:
        TelebotUtils.remove_inline_buttons_with_delay(
          bot = bot,
          chat_id = chat_id,
          message_id = call.message.message_id,
          delay = TelebotConstants.buttons_remove_delay_sec,
        )

        # No active sequential step for this chat
        return

      step_idx = state.current_step
      options_array = state.options
      if step_idx >= len(options_array):
        return

      clean_data = call.data[len(SequentialChoices._seq_prefix):]
      if not clean_data in options_array[step_idx].values():
        return

      message_id = state.message_id
      max_per_row = state.max_per_row

      # Save the choice (without prefix)
      state.results.append(clean_data)
      state.current_step += 1

      bot.answer_callback_query(call.id)

      # If last step, call final callback
      if state.current_step >= len(options_array):
        TelebotUtils.remove_inline_buttons_with_delay(
          bot = bot,
          chat_id = chat_id,
          message_id = message_id,
          delay = TelebotConstants.buttons_remove_delay_sec,
        )

        state.final_callback(chat_id, state.results)
        del SequentialChoices._step_states[chat_id]
        return

      # Otherwise, send next step buttons
      next_options = options_array[state.current_step]
      keyboard = TelebotUtils.get_keyboard_for_choices(next_options, max_per_row, SequentialChoices._seq_prefix)

      try:
        bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = keyboard)
      except Exception as e:
        bot.send_message(chat_id, str(e))
