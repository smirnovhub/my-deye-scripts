import telebot
from typing import Callable, Dict, List

from telebot_constants import buttons_remove_delay_sec
from telebot_utils import remove_inline_buttons_with_delay

# === Constants for callback_data ===
_confirm_yes = '_confirm_yes_'
_confirm_no = '_confirm_no_'
_choice_prefix = '_choice_'

# === Global storages for callbacks (by message_id) ===
_confirm_callbacks: Dict[int, Callable[[int, bool], None]] = {}
_choice_callbacks: Dict[int, Callable[[int, str], None]] = {}

def ask_confirmation(
  bot: telebot.TeleBot,
  chat_id: int,
  text: str,
  callback: Callable[[int, bool], None],
) -> telebot.types.Message:
  """
  Sends a message to the specified chat with an inline keyboard that contains
  two options: "Yes" and "No". This function is typically used when the bot
  needs to ask the user for confirmation before proceeding with an action.

  Once the message is sent, the bot stores the provided callback function
  and waits for the user's response. When the user either presses a button
  or manually types a response, the stored callback is invoked with the
  following arguments:

    - chat_id (int): the ID of the chat where the confirmation was requested.
    - result (bool): True if the user confirmed (pressed "Yes" or typed "yes"),
                     False otherwise.

  Parameters:
    bot (telebot.TeleBot): The bot instance used to send messages and handle input.
    chat_id (int): The unique Telegram chat identifier where the confirmation should be sent.
    text (str): The text of the confirmation message shown above the Yes/No buttons.
    callback (Callable[[int, bool], None]): A function that will be executed once the
                                            user responds. Receives chat_id and a boolean
                                            indicating the confirmation result.
  
  Returns:
    telebot.types.Message: The message object that was sent to the chat.
  """
  keyboard = telebot.types.InlineKeyboardMarkup()
  yes_btn = telebot.types.InlineKeyboardButton("Yes", callback_data = _confirm_yes)
  no_btn = telebot.types.InlineKeyboardButton("No", callback_data = _confirm_no)
  keyboard.row(yes_btn, no_btn)

  message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = "HTML")

  _confirm_callbacks[message.message_id] = callback

  bot.clear_step_handler_by_chat_id(message.chat.id)
  bot.register_next_step_handler(
    message,
    _user_confirmation_next_step_handler,
    bot,
    message.message_id,
  )

  return message

def _user_confirmation_next_step_handler(message: telebot.types.Message, bot: telebot.TeleBot, message_id: int):
  """
  Handles user input after a confirmation message is sent.
  - Removes the inline keyboard from the original message.
  - If input is a command, forwards it to normal command handling.
  - Otherwise, retrieves the stored callback and calls it with a boolean
    result based on whether the input equals "yes".
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

  callback = _confirm_callbacks.pop(message_id, None)
  if callback:
    callback(message.chat.id, message.text.lower() == 'yes')

def ask_choice(
  bot: telebot.TeleBot,
  chat_id: int,
  text: str,
  options: List[str],
  callback: Callable[[int, str], None],
  max_per_row: int = 5,
  wrong_choice_text: str = 'No such option',
) -> telebot.types.Message:
  """
  Sends a message to the specified chat with an inline keyboard containing
  a list of options for the user to choose from. Each option is displayed
  as a separate button. This function is typically used when the bot needs
  the user to select one item from a predefined set of strings.

  Once the message is sent, the bot stores the provided callback function
  and waits for the user’s response. When the user either presses one of
  the inline buttons or manually types a valid option, the stored callback
  is invoked with the following arguments:

    - chat_id (int): the ID of the chat where the choice was requested.
    - choice (str): the option selected by the user.

  If the user types a response that does not match any of the available
  options, the bot replies with the message specified in `wrong_choice_text`.

  Parameters:
    bot (telebot.TeleBot): The bot instance used to send messages and handle input.
    chat_id (int): The unique Telegram chat identifier where the choice should be presented.
    text (str): The text of the message shown above the choice buttons.
    options (List[str]): A list of string options to present as choices.
    callback (Callable[[int, str], None]): A function that will be executed once the
                                           user responds. Receives chat_id and the
                                           chosen option string.
    max_per_row (int, optional): Maximum number of buttons per row in the inline
                                 keyboard. Defaults to 5.
    wrong_choice_text (str, optional): The message sent when the user enters a value
                                       that does not match any available option.
                                       Defaults to "No such option".
  
  Returns:
    telebot.types.Message: The message object that was sent to the chat.
  """
  if not options:
    return bot.send_message(chat_id, text, parse_mode = "HTML")

  keyboard = telebot.types.InlineKeyboardMarkup()
  row: List[telebot.types.InlineKeyboardButton] = []

  for idx, option in enumerate(options, start = 1):
    btn = telebot.types.InlineKeyboardButton(option, callback_data = f"{_choice_prefix}{option}_")
    row.append(btn)

    if len(row) == max_per_row or idx == len(options):
      keyboard.row(*row)
      row = []

  message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = "HTML")

  _choice_callbacks[message.message_id] = callback

  bot.clear_step_handler_by_chat_id(message.chat.id)
  bot.register_next_step_handler(
    message,
    _user_choice_next_step_handler,
    bot,
    message.message_id,
    options,
    wrong_choice_text,
  )

  return message

def ask_advanced_choice(
  bot: telebot.TeleBot,
  chat_id: int,
  text: str,
  options: Dict[str, str],
  max_per_row: int = 5,
) -> telebot.types.Message:
  """
  Sends a message with an inline keyboard for the user to select from
  multiple options, where keys are internal identifiers and values are labels.

  If the options dictionary is empty, sends the message without a keyboard.

  Stores the callback function in a dictionary keyed by the message ID
  and clears any previous step handlers for the chat.

  Parameters:
    bot: TeleBot instance to send messages and handle input.
    chat_id: Target chat ID.
    text: Message displayed above the buttons.
    options: Dictionary mapping option keys to display labels.
    callback: Function to be called later with the chat ID and chosen key.
    max_per_row: Maximum buttons per row (default 5).
    wrong_choice_text: Message sent for invalid input (default "No such option").

  Returns:
    telebot.types.Message: The message object that was sent to the chat.
  """
  if not options:
    return bot.send_message(chat_id, text, parse_mode = "HTML")

  keyboard = get_keyboard_for_choices(options, max_per_row)
  message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = "HTML")

  bot.clear_step_handler_by_chat_id(message.chat.id)
  bot.register_next_step_handler(
    message,
    _user_advanced_choice_next_step_handler,
    bot,
    message.message_id,
  )

  return message

def _user_choice_next_step_handler(message: telebot.types.Message, bot: telebot.TeleBot, message_id: int,
                                   options: List[str], wrong_choice_text: str):
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

  choice = message.text
  if choice in options:
    callback = _choice_callbacks.pop(message_id, None)
    if callback:
      callback(message.chat.id, choice)
  elif wrong_choice_text:
    bot.send_message(message.chat.id, wrong_choice_text, parse_mode = "HTML")

def _user_advanced_choice_next_step_handler(message: telebot.types.Message, bot: telebot.TeleBot, message_id: int):
  """
  Handles the user's response after an advanced choice message is sent.
  - Removes the inline keyboard from the original message.
  - If the user sent a command (text starting with '/'), forwards it to
    the normal command handler.
  - Otherwise, does not process input (callback handling is not included
    in this function).
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

def register_global_handler_for_user_choices(bot: telebot.TeleBot) -> None:
  """
  Registers a global callback query handler that processes both simple
  confirmations (two-button answers) and multiple-choice selections.

  The handler:
    - Catches all button presses related to confirmations or choices.
    - Acknowledges the press to stop the client’s loading animation.
    - Removes the inline keyboard from the original message.
    - Clears any pending step handlers for the chat.

  For confirmations, it resolves the user’s answer to a boolean value
  and calls the stored callback with (chat_id, result).

  For choices, it extracts the selected option text and calls the
  stored callback with (chat_id, option).
  """
  @bot.callback_query_handler(
    func = lambda call: (call.data in (_confirm_yes, _confirm_no) or call.data.startswith(_choice_prefix)))
  def handle(call: telebot.types.CallbackQuery):
    """Handle Yes/No and choice buttons with one handler."""
    bot.answer_callback_query(call.id)

    remove_inline_buttons_with_delay(
      bot = bot,
      chat_id = call.message.chat.id,
      message_id = call.message.message_id,
      delay = buttons_remove_delay_sec,
    )

    # Clear any pending next-step handlers for this chat
    bot.clear_step_handler_by_chat_id(call.message.chat.id)

    # === Handle confirmation ===
    if call.data in (_confirm_yes, _confirm_no):
      result = call.data == _confirm_yes
      callback = _confirm_callbacks.pop(call.message.message_id, None)
      if callback:
        callback(call.message.chat.id, result)
      return

    # === Handle choice ===
    if call.data.startswith(_choice_prefix):
      choice = call.data[len(_choice_prefix):-1] # strip prefix & trailing "_"
      callback = _choice_callbacks.pop(call.message.message_id, None)
      if callback:
        callback(call.message.chat.id, choice)

def get_keyboard_for_choices(options: Dict[str, str], max_per_row: int) -> telebot.types.InlineKeyboardMarkup:
  """
  Build an inline keyboard where:
    - keys of the dict are button texts,
    - values of the dict are callback_data strings.
  Buttons are arranged in rows with up to max_per_row buttons each.
  An empty string as a key forces a line break (starts a new row).
  """
  keyboard = telebot.types.InlineKeyboardMarkup()
  row: List[telebot.types.InlineKeyboardButton] = []

  for idx, (text, data) in enumerate(options.items(), start = 1):
    if text == "":
      # Commit the current row (if not empty) and start a new one
      if row:
        keyboard.row(*row)
        row = []
      continue

    btn = telebot.types.InlineKeyboardButton(text, callback_data = data)
    row.append(btn)

    # Commit row if it's full
    if len(row) == max_per_row:
      keyboard.row(*row)
      row = []

  # Add remaining buttons in the last row
  if row:
    keyboard.row(*row)

  return keyboard
