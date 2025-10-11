import telebot

from typing import Dict, Callable, cast
from dataclasses import dataclass

from telebot_utils import TelebotUtils
from telebot_constants import TelebotConstants

@dataclass
class AdvancedChoiceButton:
  text: str
  data: str

class AdvancedChoice:
  _choice_callbacks: Dict[int, Callable[[int, AdvancedChoiceButton], None]] = {}
  _choice_prefix = '_adv_choice_'
  _is_global_handler_registered = False

  @staticmethod
  def ask_advanced_choice(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    options: Dict[str, str],
    callback: Callable[[int, AdvancedChoiceButton], None],
    max_per_row: int = 5,
  ) -> telebot.types.Message:
    """
    Sends a message to the specified chat with an inline keyboard containing
    a list of options for the user to choose from. Each option has a display
    text and an associated data value.

    When the user presses a button, the provided callback is called with a
    dictionary containing 'text' and 'data' of the chosen option.

    Parameters:
        bot (telebot.TeleBot): The bot instance used to send messages.
        chat_id (int): The Telegram chat ID where the message should be sent.
        text (str): The text shown above the choice buttons.
        options (Dict[str, str]): Mapping from button text to associated data.
        callback (Callable[[int, Dict[str, str]]]): Function called when the user
                                                      presses a button. Receives
                                                      chat_id and dict with
                                                      'text' and 'data'.
        max_per_row (int, optional): Maximum number of buttons per row. Default is 5.

    Returns:
        telebot.types.Message: The sent message object.
    """
    if not options:
      return bot.send_message(chat_id, text, parse_mode = 'HTML')

    # Ensure the global callback handler is registered
    AdvancedChoice._register_global_handler(bot)

    # Create callback_data mapping for buttons
    # Format: _choice_prefix + button_text + "_" to identify button presses
    options_dict = {text: f"{AdvancedChoice._choice_prefix}{data}_" for text, data in options.items()}

    # Generate inline keyboard
    keyboard = TelebotUtils.get_keyboard_for_choices(options_dict, max_per_row)

    # Send message with inline keyboard
    message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = 'HTML')

    # Store callback function associated with this message
    AdvancedChoice._choice_callbacks[message.message_id] = callback

    bot.register_next_step_handler(
      message,
      AdvancedChoice._user_advanced_choice_next_step_handler,
      bot,
      message.message_id,
      text,
    )

    return message

  @staticmethod
  def _register_global_handler(bot: telebot.TeleBot) -> None:
    """
    Registers a global callback query handler for multiple-choice selections.

    This handler:
      - Captures all button presses that start with `_choice_prefix`.
      - Acknowledges the button press.
      - Removes inline buttons after a short delay.
      - Invokes the stored callback with a dictionary containing 'text' and 'data'.
    """
    if AdvancedChoice._is_global_handler_registered:
      return

    AdvancedChoice._is_global_handler_registered = True

    @bot.callback_query_handler(func = lambda call: call.data.startswith(AdvancedChoice._choice_prefix))
    def handle(call: telebot.types.CallbackQuery):
      """Handle inline button presses for advanced choices."""
      bot.answer_callback_query(call.id)

      TelebotUtils.remove_inline_buttons_with_delay(
        bot = bot,
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        delay = TelebotConstants.buttons_remove_delay_sec,
      )

      if call.data.startswith(AdvancedChoice._choice_prefix):
        callback = AdvancedChoice._choice_callbacks.pop(call.message.message_id, None)
        if callback:
          choice_text = call.data[len(AdvancedChoice._choice_prefix):-1] # strip prefix & trailing "_"
          # Build dictionary with button text and associated data
          button = TelebotUtils.get_inline_button_by_data(cast(telebot.types.Message, call.message), str(call.data))
          choice = AdvancedChoiceButton(text = button.text if button else 'unknown', data = choice_text)

          try:
            bot.edit_message_text(
              f'{call.message.text} {choice.text}',
              chat_id = call.message.chat.id,
              message_id = call.message.message_id,
              parse_mode = 'HTML',
            )
          except Exception:
            pass

          callback(call.message.chat.id, choice)

  @staticmethod
  def _user_advanced_choice_next_step_handler(
    message: telebot.types.Message,
    bot: telebot.TeleBot,
    message_id: int,
    text: str,
  ):
    """
    Handles the user's response after an advanced choice message is sent.
    - Removes the inline keyboard from the original message.
    - If the user sent a command (text starting with '/'), forwards it to
      the normal command handler.
    - Otherwise, does not process input (callback handling is not included
      in this function).
    """
    TelebotUtils.remove_inline_buttons_with_delay(
      bot = bot,
      chat_id = message.chat.id,
      message_id = message_id,
      delay = TelebotConstants.buttons_remove_delay_sec,
    )

    try:
      bot.edit_message_text(
        f'{text} skipped',
        chat_id = message.chat.id,
        message_id = message_id,
        parse_mode = 'HTML',
      )
    except Exception:
      pass

    # if we received new command, process it
    if message.text.startswith('/'):
      bot.process_new_messages([message])
