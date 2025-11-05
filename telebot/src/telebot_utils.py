import os
import threading
import time
import telebot

from typing import Dict, List, Optional

class TelebotUtils:
  row_break_str = '!break!'

  @staticmethod
  def get_inline_button_by_data(
    message: telebot.types.Message,
    button_data: str,
  ) -> Optional[telebot.types.InlineKeyboardButton]:
    """
    Retrieve an InlineKeyboardButton from a message by its callback_data.

    :param message: The Telegram message containing the inline keyboard
    :param button_data: The callback_data of the button to search for
    :return: The InlineKeyboardButton if found, otherwise None
    """
    # Get the reply_markup (inline keyboard) from the message
    markup = message.reply_markup
    if markup is None:
      return None

    # Iterate through each row of buttons in the keyboard
    for row in markup.keyboard:
      # Iterate through each button in the row
      for btn in row:
        # Check if the button's callback_data matches the requested data
        if btn.callback_data == button_data:
          return btn

    return None

  @staticmethod
  def get_inline_button_by_text(
    message: telebot.types.Message,
    button_text: str,
  ) -> Optional[telebot.types.InlineKeyboardButton]:
    """
    Retrieve an InlineKeyboardButton from a message by its text.

    :param message: The Telegram message containing the inline keyboard
    :param button_text: The text of the button to search for
    :return: The InlineKeyboardButton if found, otherwise None
    """
    markup = message.reply_markup
    if markup is None:
      return None

    for row in markup.keyboard:
      for btn in row:
        if btn.text == button_text:
          return btn

    return None

  @staticmethod
  def remove_inline_buttons(bot: telebot.TeleBot, chat_id: int, message_id: int) -> None:
    """
    Safely remove inline buttons from a message.
    
    :param bot: TeleBot instance
    :param chat_id: Chat ID where the message was sent
    :param message_id: ID of the message to update
    """
    try:
      bot.edit_message_reply_markup(chat_id = chat_id, message_id = message_id, reply_markup = None)
    except Exception:
      # Ignore errors (e.g., already removed, message deleted, not modified)
      pass

  @staticmethod
  def remove_inline_buttons_with_delay(bot: telebot.TeleBot, chat_id: int, message_id: int, delay: float) -> None:
    """
    Schedule removal of inline buttons from a message after a delay.

    :param bot: TeleBot instance
    :param chat_id: Chat ID where the message was sent
    :param message_id: ID of the message
    :param delay: Time in seconds before removing buttons
    """
    if delay < 0.01:
      TelebotUtils.remove_inline_buttons(bot, chat_id, message_id)
      return

    timer = threading.Timer(delay, lambda: TelebotUtils.remove_inline_buttons(bot, chat_id, message_id))
    timer.daemon = True # thread won't block program exit
    timer.start()

  @staticmethod
  def get_keyboard_for_choices(
    options: Dict[str, str],
    max_per_row: int,
    data_prefix: str = '',
  ) -> telebot.types.InlineKeyboardMarkup:
    """
    Build an inline keyboard where:
      - keys of the dict are button texts,
      - values of the dict are callback_data strings.
    Buttons are arranged in rows with up to max_per_row buttons each.
    An empty string as a key forces a line break (starts a new row).
    """
    keyboard = telebot.types.InlineKeyboardMarkup()
    row: List[telebot.types.InlineKeyboardButton] = []

    for text, data in options.items():
      if TelebotUtils.row_break_str in (text, data):
        # Commit the current row (if not empty) and start a new one
        if row:
          keyboard.row(*row)
          row = []
        continue

      btn = telebot.types.InlineKeyboardButton(text, callback_data = data_prefix + data)
      row.append(btn)

      # Commit row if it's full
      if len(row) == max_per_row:
        keyboard.row(*row)
        row = []

    # Add remaining buttons in the last row
    if row:
      keyboard.row(*row)

    return keyboard

  @staticmethod
  def make_callback_query_filter(prefix: str):
    """
    Creates a callback query filter function for use with TeleBot's
    `callback_query_handler`.

    The returned function checks whether the received `CallbackQuery`
    object has non-empty `data` and whether it starts with the specified
    prefix string. Useful for registering different handlers for
    callback commands with distinct prefixes.

    Args:
        prefix (str): The prefix that `call.data` must start with (e.g., "/").

    Returns:
        A filter function compatible with `callback_query_handler(func=...)`
        that returns True when the callback data starts with the given prefix.
    """
    def filter_func(call):
      return isinstance(call, telebot.types.CallbackQuery) and call.data and call.data.startswith(prefix)

    return filter_func

  @staticmethod
  def forward_next(bot: telebot.TeleBot, message: telebot.types.Message) -> bool:
    is_forward = message.forward_from_chat is not None and message.forward_from_chat.username is not None
    # Forward new commands or forwarded message to the bot
    if is_forward or message.text.startswith('/'):
      bot.process_new_messages([message])
      return True
    return False

  @staticmethod
  def stop_bot(bot: telebot.TeleBot):
    """
    Gracefully stops the running TeleBot instance and terminates the process.

    This method first calls `bot.stop_bot()` to stop all polling and background
    threads associated with the TeleBot instance. If the bot shuts down correctly,
    the process should naturally exit. However, as a safeguard, the method waits
    a minute and then forcefully terminates the process using `os._exit(1)`.

    Args:
        bot (telebot.TeleBot): The TeleBot instance to stop.
    """
    bot.stop_bot()
    time.sleep(60)
    # exit will never fire if bot has stopped in right way
    os._exit(1)
