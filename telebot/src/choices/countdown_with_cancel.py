import time
import telebot
import threading

from dataclasses import dataclass
from typing import Callable, Dict

from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants

@dataclass
class CountdownEntry:
  stop_event: threading.Event
  on_cancel: Callable[[int], None]
  on_finish: Callable[[int], None]
  text: str
  chat_id: int
  keyboard: telebot.types.InlineKeyboardMarkup

class CountdownWithCancel:
  # Unique prefix for countdown cancel buttons
  _countdown_prefix = "_countdown_"

  # Global storage for countdown states, keyed by message_id
  _countdown_callbacks: Dict[int, CountdownEntry] = {}

  # Flag to ensure we register the global callback handler only once per bot instance
  _is_global_handler_registered = False

  @staticmethod
  def show_countdown(
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
    # Create keyboard with one Cancel button using your helper
    cancel_keyboard = TelebotUtils.get_keyboard_for_choices(
      options = {"Cancel": "btn"},
      max_per_row = 1,
      data_prefix = CountdownWithCancel._countdown_prefix,
    )

    # Send initial message
    message = bot.send_message(chat_id, f"{text}{seconds}", reply_markup = cancel_keyboard)

    # Event used to stop the countdown
    stop_event = threading.Event()

    # Store state globally keyed by message_id so global handler can find it
    CountdownWithCancel._countdown_callbacks[message.message_id] = CountdownEntry(
      stop_event = stop_event,
      on_cancel = on_cancel,
      on_finish = on_finish,
      text = text,
      chat_id = chat_id,
      keyboard = cancel_keyboard,
    )

    CountdownWithCancel._register_global_handler(bot)

    # Register next step handler to cancel on text input
    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.register_next_step_handler(
      message,
      CountdownWithCancel._next_step_handler,
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
      CountdownWithCancel._countdown_callbacks.pop(message.message_id, None)

      stop_event.set()

      try:
        bot.delete_message(chat_id, message.message_id)
      except Exception:
        pass

      if called_from_user:
        try:
          on_cancel(chat_id)
        except Exception as e:
          bot.send_message(chat_id, str(e))
      else:
        try:
          on_finish(chat_id)
        except Exception as e:
          bot.send_message(chat_id, str(e))

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

  @staticmethod
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
      CountdownWithCancel._countdown_callbacks.pop(message_id, None)

      try:
        bot.delete_message(message.chat.id, message_id)
      except Exception:
        pass

      try:
        on_cancel(message.chat.id)
      except Exception as e:
        bot.send_message(message.chat.id, str(e))

    TelebotUtils.remove_inline_buttons_with_delay(
      bot = bot,
      chat_id = message.chat.id,
      message_id = message_id,
      delay = TelebotConstants.buttons_remove_delay_sec,
    )

    # If we received new command, process it
    if TelebotUtils.forward_next(bot, message):
      return

  # Register a single global callback_query handler (only once)
  @staticmethod
  def _register_global_handler(bot: telebot.TeleBot):
    if CountdownWithCancel._is_global_handler_registered:
      return

    CountdownWithCancel._is_global_handler_registered = True

    @bot.callback_query_handler(func = TelebotUtils.make_callback_query_filter(CountdownWithCancel._countdown_prefix))
    def _global_handle_cancel(call: telebot.types.CallbackQuery):
      """
      Global handler for Cancel buttons of countdowns.
      Looks up the message_id in the global _countdown_callbacks and
      performs cleanup based on stored state.
      """
      bot.answer_callback_query(call.id)

      msg_id = call.message.message_id
      entry = CountdownWithCancel._countdown_callbacks.pop(msg_id, None)

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

      # If not already stopped — stop and update message
      if not entry.stop_event.is_set():
        entry.stop_event.set()
        try:
          bot.delete_message(entry.chat_id, msg_id)
        except Exception:
          pass

        try:
          entry.on_cancel(entry.chat_id)
        except Exception as e:
          bot.send_message(entry.chat_id, str(e))
