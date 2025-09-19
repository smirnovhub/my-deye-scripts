import telebot
import threading
import time

from typing import Callable, Dict

from telebot_utils import remove_inline_buttons_with_delay
from telebot_user_choices_helper import get_keyboard_for_choices
from telebot_constants import buttons_remove_delay_sec

# Unique prefix for countdown cancel buttons
_countdown_prefix = "_countdown_"

# Private keys for entries in _countdown_callbacks (lowercase, private)
_stop_event_str = "stop_event"
_on_cancel_str = "on_cancel"
_on_finish_str = "on_finish"
_text_str = "text"
_chat_id_str = "chat_id"
_keyboard_str = "keyboard"

# Global storage for countdown states, keyed by message_id
# Each value is a dict with keys: 'stop_event', 'on_cancel', 'on_finish', 'text', 'chat_id', 'keyboard'
_countdown_callbacks: Dict[int, dict] = {}

# Flag to ensure we register the global callback handler only once per bot instance
_is_global_handler_registered = False

def countdown_with_cancel(
  bot: telebot.TeleBot,
  chat_id: int,
  text: str,
  seconds: int,
  on_finish: Callable[[int], None],
  on_cancel: Callable[[int], None],
):
  """
  Sends a countdown message with a "Cancel" button.

  Behavior:
    - Updates the message every second with the remaining time.
    - If user presses "Cancel" or sends any message, countdown is stopped and on_cancel(chat_id) is called.
    - If countdown reaches zero, Cancel button is removed and on_finish(chat_id) is called.
    - Final message shows "done" or "cancelled" instead of the number.

  Args:
      bot: telebot.TeleBot instance.
      chat_id: Telegram chat ID.
      text: Base text to display.
      seconds: Countdown duration in seconds.
      on_finish: Callback executed when countdown ends normally. Receives chat_id.
      on_cancel: Optional callback executed when countdown is cancelled. Receives chat_id.
  """
  # --- Create keyboard with one Cancel button using your helper ---
  cancel_keyboard = get_keyboard_for_choices(
    options = {"Cancel": "btn"},
    max_per_row = 1,
    data_prefix = _countdown_prefix,
  )

  # Send initial message
  message = bot.send_message(chat_id, f"{text}{seconds}", reply_markup = cancel_keyboard)

  # Event used to stop the countdown
  stop_event = threading.Event()

  # Store state globally keyed by message_id so global handler can find it
  _countdown_callbacks[message.message_id] = {
    _stop_event_str: stop_event,
    _on_cancel_str: on_cancel,
    _on_finish_str: on_finish,
    _text_str: text,
    _chat_id_str: chat_id,
    _keyboard_str: cancel_keyboard,
  }

  _register_global_handler(bot)

  # Register next step handler to cancel on text input
  bot.clear_step_handler_by_chat_id(message.chat.id)
  bot.register_next_step_handler(
    message,
    _next_step_handler,
    bot,
    message.message_id,
    stop_event,
    on_cancel,
  )

  def stop_and_cleanup_local(called_from_user: bool):
    """
    Local helper: ensure we stop event and remove entry from global map (if still present).
    This function keeps behavior consistent when countdown_loop finishes locally.
    """
    # Remove entry if still present
    _countdown_callbacks.pop(message.message_id, None)

    stop_event.set()
    try:
      bot.delete_message(chat_id, message.message_id)
    except Exception:
      pass

    if called_from_user:
      if on_cancel:
        try:
          on_cancel(chat_id)
        except Exception:
          pass
    else:
      try:
        on_finish(chat_id)
      except Exception:
        pass

  def countdown_loop():
    for sec_left in range(seconds - 1, -1, -1):
      if stop_event.is_set():
        return
      time.sleep(1)

      if stop_event.is_set():
        return

      if sec_left == 0:
        # Finished normally
        stop_and_cleanup_local(False)
        return

      try:
        bot.edit_message_text(
          f"{text}{sec_left}",
          chat_id,
          message.message_id,
          reply_markup = cancel_keyboard,
        )
      except Exception:
        pass

  # Launch background countdown
  threading.Thread(target = countdown_loop, daemon = True).start()

def _next_step_handler(
  message: telebot.types.Message,
  bot: telebot.TeleBot,
  message_id: int,
  stop_event: threading.Event,
  on_cancel: Callable[[int], None],
):
  """
  Handles the user's response after countdown is started.
  - Cancels countdown on any text input.
  - Removes the inline keyboard from the original message.
  - If the user sent a command (text starting with '/'), forwards it to
    the normal command handler.
  """

  # If countdown still running — stop it and update the original countdown message
  if not stop_event.is_set():
    stop_event.set()

    # Remove global entry for this message if it exists
    _countdown_callbacks.pop(message_id, None)

    try:
      bot.delete_message(message.chat.id, message_id)
    except Exception:
      pass

    if on_cancel:
      try:
        on_cancel(message.chat.id)
      except Exception:
        pass

  remove_inline_buttons_with_delay(
    bot = bot,
    chat_id = message.chat.id,
    message_id = message_id,
    delay = buttons_remove_delay_sec,
  )

  # If we received new command, process it
  if message.text.startswith('/'):
    bot.process_new_messages([message])
    return

# Register a single global callback_query handler (only once)
def _register_global_handler(bot: telebot.TeleBot):
  global _is_global_handler_registered
  if _is_global_handler_registered:
    return

  _is_global_handler_registered = True

  @bot.callback_query_handler(func = lambda call: call.data.startswith(_countdown_prefix))
  def _global_handle_cancel(call: telebot.types.CallbackQuery):
    """
    Global handler for Cancel buttons of countdowns.
    Looks up the message_id in the global _countdown_callbacks and
    performs cleanup based on stored state.
    """
    bot.answer_callback_query(call.id)

    msg_id = call.message.message_id
    entry = _countdown_callbacks.pop(msg_id, None)

    if entry is None:
      # No active countdown for this message — try to remove buttons if any
      try:
        bot.edit_message_reply_markup(
          chat_id = call.message.chat.id,
          message_id = msg_id,
          reply_markup = None,
        )
      except Exception:
        pass
      return

    stop_event_local = entry[_stop_event_str]
    chat_id_local = entry[_chat_id_str]
    on_cancel_local = entry[_on_cancel_str]

    # If not already stopped — stop and update message
    if not stop_event_local.is_set():
      stop_event_local.set()
      try:
        bot.delete_message(chat_id_local, msg_id)
      except Exception:
        pass

      if on_cancel_local:
        try:
          on_cancel_local(chat_id_local)
        except Exception:
          pass
