import telebot
from typing import Callable, Dict, List

# === Constants for callback_data ===
CONFIRM_YES = '_confirm_yes_'
CONFIRM_NO = '_confirm_no_'
CHOICE_PREFIX = '_choice_'

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
  Send a Yes/No inline keyboard and register `callback(chat_id, result: bool)`
  to be called when the user presses a button.
  """
  keyboard = telebot.types.InlineKeyboardMarkup()
  yes_btn = telebot.types.InlineKeyboardButton("Yes", callback_data = CONFIRM_YES)
  no_btn = telebot.types.InlineKeyboardButton("No", callback_data = CONFIRM_NO)
  keyboard.row(yes_btn, no_btn)

  message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = "HTML")
  _confirm_callbacks[message.message_id] = callback
  return message

def ask_choice(
  bot: telebot.TeleBot,
  chat_id: int,
  text: str,
  options: List[str],
  max_per_row: int,
  callback: Callable[[int, str], None],
) -> telebot.types.Message:
  """
  Send a choice inline keyboard and register `callback(chat_id, choice: str)`
  to be called when the user presses a button.
  """
  keyboard = telebot.types.InlineKeyboardMarkup()
  row: List[telebot.types.InlineKeyboardButton] = []

  for idx, option in enumerate(options, start = 1):
    btn = telebot.types.InlineKeyboardButton(option, callback_data = f"{CHOICE_PREFIX}{option}_")
    row.append(btn)

    if len(row) == max_per_row or idx == len(options):
      keyboard.row(*row)
      row = []

  message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = "HTML")
  _choice_callbacks[message.message_id] = callback
  return message

def register_global_handler_for_user_choices(bot: telebot.TeleBot) -> None:
  """
  Register a single global callback_query_handler that processes both
  confirmation and choice buttons.
  """
  @bot.callback_query_handler(
    func = lambda call: (call.data in (CONFIRM_YES, CONFIRM_NO) or call.data.startswith(CHOICE_PREFIX)))
  def handle(call: telebot.types.CallbackQuery):
    """Handle Yes/No and choice buttons with one handler."""
    bot.answer_callback_query(call.id)

    try:
      # Remove inline keyboard
      bot.edit_message_reply_markup(
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        reply_markup = None,
      )
    except Exception:
      # Ignore errors like "message is not modified"
      pass

    # Clear any pending next-step handlers for this chat
    bot.clear_step_handler_by_chat_id(call.message.chat.id)

    # === Handle confirmation ===
    if call.data in (CONFIRM_YES, CONFIRM_NO):
      result = call.data == CONFIRM_YES
      callback = _confirm_callbacks.pop(call.message.message_id, None)
      if callback:
        callback(call.message.chat.id, result)
      return

    # === Handle choice ===
    if call.data.startswith(CHOICE_PREFIX):
      choice = call.data[len(CHOICE_PREFIX):-1]  # strip prefix & trailing "_"
      callback = _choice_callbacks.pop(call.message.message_id, None)
      if callback:
        callback(call.message.chat.id, choice)

def get_keyboard_for_choices(options: Dict[str, str], max_per_row: int) -> telebot.types.InlineKeyboardMarkup:
  """
  Build an inline keyboard where:
    - keys of the dict are button texts,
    - values of the dict are callback_data strings.
  Buttons are arranged in rows with up to max_per_row buttons each.
  """
  keyboard = telebot.types.InlineKeyboardMarkup()
  row: List[telebot.types.InlineKeyboardButton] = []

  # enumerate is not needed here because we iterate over dict items
  for idx, (text, data) in enumerate(options.items(), start = 1):
    # Create a button with given text and callback data
    btn = telebot.types.InlineKeyboardButton(text, callback_data = data)
    row.append(btn)

    # If row is full OR last element → add row to keyboard
    if len(row) == max_per_row or idx == len(options):
      keyboard.row(*row)
      row = []

  return keyboard
