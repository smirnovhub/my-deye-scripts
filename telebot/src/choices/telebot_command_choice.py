import telebot
from typing import Dict

from telebot_constants import buttons_remove_delay_sec
from telebot_user_choices_helper import get_keyboard_for_choices
from telebot_utils import remove_inline_buttons_with_delay

def ask_command_choice(
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
    _user_command_choice_next_step_handler,
    bot,
    message.message_id,
  )

  return message

def _user_command_choice_next_step_handler(message: telebot.types.Message, bot: telebot.TeleBot, message_id: int):
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
