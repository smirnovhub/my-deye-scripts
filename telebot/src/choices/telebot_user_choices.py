import telebot
from typing import Callable, Dict, List

from telebot_constants import TelebotConstants
from telebot_utils import TelebotUtils

class UserChoices:
  # Constant for callback_data
  _choice_prefix = '_choice_'

  # Global storages for callbacks (by message_id)
  _choice_callbacks: Dict[int, Callable[[int, str], None]] = {}

  # Flag to ensure we register the global callback handler only once per bot instance
  _is_global_handler_registered = False

  @staticmethod
  def ask_confirmation(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    callback: Callable[[int, bool], None],
  ) -> telebot.types.Message:
    """
    Sends a message with a confirmation prompt using an inline keyboard.

    This function displays two buttons: "Yes" and "No". The user can either
    press a button or type a response manually. Any typed input other than
    "yes" (case-insensitive) is considered False. The resulting boolean is
    passed to the provided callback function.

    Parameters:
      bot (telebot.TeleBot): The bot instance used to send messages and handle input.
      chat_id (int): The Telegram chat ID where the confirmation should be sent.
      text (str): The text of the confirmation message shown above the buttons.
      callback (Callable[[int, bool], None]): Function to execute when the user
                                              responds. Receives the chat_id
                                              and a boolean indicating confirmation
                                              (True for "Yes", False for "No").

    Returns:
      telebot.types.Message: The message object that was sent to the chat.
    """

    # Options for confirmation
    options = ['Yes', 'No']

    # Internal callback to translate choice into a boolean result
    def _internal_choice_cb(chat_id_inner: int, choice: str):
      callback(chat_id_inner, choice.lower() == 'yes')

    # Use ask_choice to send buttons and handle user response
    return UserChoices.ask_choice(
      bot,
      chat_id,
      text,
      options,
      _internal_choice_cb,
      accept_wrong_choice_from_user_input = True,
    )

  @staticmethod
  def ask_choice(
    bot: telebot.TeleBot,
    chat_id: int,
    text: str,
    options: List[str],
    callback: Callable[[int, str], None],
    max_per_row: int = 5,
    accept_wrong_choice_from_user_input: bool = False,
    wrong_choice_text: str = 'No such option',
  ) -> telebot.types.Message:
    """
    Sends a message to the specified chat with an inline keyboard containing
    a list of options for the user to choose from. Each option is displayed
    as a separate button. This function is typically used when the bot needs
    the user to select one item from a predefined set of strings.

    Once the message is sent, the bot stores the provided callback function
    and waits for the user's response. When the user either presses one of
    the inline buttons or manually types a valid option, the stored callback
    is invoked with the following arguments:

      - chat_id (int): the ID of the chat where the choice was requested.
      - choice (str): the option selected by the user.

    If the user types a response that does not match any of the available
    options:
      - If `accept_wrong_choice_from_user_input` is True, the input is accepted
        and passed to the callback as-is.
      - Otherwise, the bot replies with the message specified in `wrong_choice_text`.

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
      accept_wrong_choice_from_user_input (bool, optional): If True, the bot will accept
                                  any text input from the user even if it does not
                                  match the predefined options. Defaults to False.
      wrong_choice_text (str, optional): The message sent when the user enters a value
                                        that does not match any available option
                                        and `accept_wrong_choice_from_user_input` is False.
                                        Defaults to "No such option".
    
    Returns:
      telebot.types.Message: The message object that was sent to the chat.
    """
    if not options:
      return bot.send_message(chat_id, text, parse_mode = 'HTML')

    # Register global handler for buttons
    UserChoices._register_global_handler(bot)

    # Build a dictionary for buttons where:
    # - the key is the button text (option)
    # - the value is the callback_data for the button
    options_dict = {option: f"{UserChoices._choice_prefix}{option}_" for option in options}

    # Generate the inline keyboard using the helper function
    # Buttons will be arranged in rows with up to `max_per_row` buttons per row
    keyboard = TelebotUtils.get_keyboard_for_choices(options_dict, max_per_row)

    message = bot.send_message(chat_id, text, reply_markup = keyboard, parse_mode = 'HTML')

    UserChoices._choice_callbacks[message.message_id] = callback

    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.register_next_step_handler(
      message,
      UserChoices._user_choice_next_step_handler,
      bot,
      message.message_id,
      options,
      accept_wrong_choice_from_user_input,
      wrong_choice_text,
    )

    return message

  @staticmethod
  def _user_choice_next_step_handler(
    message: telebot.types.Message,
    bot: telebot.TeleBot,
    message_id: int,
    options: List[str],
    accept_wrong_choice_from_user_input: bool,
    wrong_choice_text: str,
  ):
    """
    Handles user input after a choice message is sent.

    - Removes the inline keyboard from the original message.
    - If the user sends a command (text starting with '/'), forwards it to
      normal command handling.
    - If the input matches one of the valid options or if
      `accept_wrong_choice_from_user_input` is True, calls the stored callback
      with the input.
    - Otherwise, sends the `wrong_choice_text` message to inform the user of
      invalid input.

    Parameters:
      message (telebot.types.Message): The message object received from the user.
      bot (telebot.TeleBot): The bot instance used to send messages and handle input.
      message_id (int): The ID of the message containing the inline keyboard.
      options (List[str]): A list of valid options that the user can choose from.
      accept_wrong_choice_from_user_input (bool): If True, any user input is accepted
                                                  and passed to the callback.
      wrong_choice_text (str): The message to send when the user input is invalid
                              and `accept_wrong_choice_from_user_input` is False.
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

    choice = message.text
    if choice is not None and (choice in options or accept_wrong_choice_from_user_input):
      callback = UserChoices._choice_callbacks.pop(message_id, None)
      if callback:
        callback(message.chat.id, choice)
    elif wrong_choice_text:
      bot.send_message(message.chat.id, wrong_choice_text, parse_mode = 'HTML')

  @staticmethod
  def _register_global_handler(bot: telebot.TeleBot) -> None:
    """
    Registers a global callback query handler for multiple-choice selections.

    The handler:
      - Catches all button presses that start with the choice prefix (`_choice_prefix`).
      - Acknowledges the press to stop the client's loading animation.
      - Removes the inline keyboard from the original message.
      - Clears any pending step handlers for the chat.

    When a choice button is pressed:
      - The callback associated with the message is retrieved.
      - The selected choice text is extracted from the callback_data.
      - The stored callback is invoked with (chat_id, choice).

    Notes:
      - The function only handles inline button presses; typed responses
        are handled separately in `_user_choice_next_step_handler`.
      - The trailing underscore in the callback_data is stripped before
        passing the choice to the callback.
    """
    if UserChoices._is_global_handler_registered:
      return

    UserChoices._is_global_handler_registered = True

    @bot.callback_query_handler(func = lambda call: call.data.startswith(UserChoices._choice_prefix))
    def handle(call: telebot.types.CallbackQuery):
      """Handle choice buttons with one handler."""
      bot.answer_callback_query(call.id)

      TelebotUtils.remove_inline_buttons_with_delay(
        bot = bot,
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        delay = TelebotConstants.buttons_remove_delay_sec,
      )

      # Clear any pending next-step handlers for this chat
      bot.clear_step_handler_by_chat_id(call.message.chat.id)

      # Handle choice
      if call.data.startswith(UserChoices._choice_prefix):
        choice = call.data[len(UserChoices._choice_prefix):-1] # strip prefix & trailing "_"
        callback = UserChoices._choice_callbacks.pop(call.message.message_id, None)
        if callback:
          callback(call.message.chat.id, choice)
