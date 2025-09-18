import telebot
from typing import List, cast

from telebot_fake_message import TelebotFakeMessage
from telebot_menu_item_handler import TelebotMenuItemHandler

from telebot_constants import buttons_remove_delay_sec
from telebot_utils import remove_inline_buttons_with_delay

def register_global_callback_handler_for_hidden_command_from_button(bot: telebot.TeleBot,
                                                                    items: List[TelebotMenuItemHandler]):
  """
  Registers a global callback query handler that intercepts inline button
  presses representing "hidden" commands (buttons whose callback data
  starts with a special character, e.g., '#').

  When such a button is pressed, the handler:
    1. Creates a fake Message object containing the command text, so the
       bot can process it as if the user had typed it manually.
    2. Acknowledges the callback query to stop the client’s loading animation.
    3. Removes the inline keyboard from the original message.
    4. Searches through the provided list of menu items and calls the
       processing function of the matching command.

  Parameters:
    bot (telebot.TeleBot): The bot instance to which the handler is attached.
    items (List[TelebotMenuItemHandler]): A list of menu items, each with
                                          a command and a processing method.
  """
  @bot.callback_query_handler(func = lambda call: call.data and call.data.startswith('#'))
  def handle(call: telebot.types.CallbackQuery):
    if call.data:
      # command without leading '#'
      command = call.data[1:]

      # If callback_data looks like a command (starts with '#'),
      # we create a fake Message object that contains this command.
      fake_message = TelebotFakeMessage(
        cast(telebot.types.Message, call.message), # original message object
        command, # command text without trailing # (e.g. "status")
        call.from_user, # user who clicked the button
      )

      bot.answer_callback_query(call.id)

      remove_inline_buttons_with_delay(
        bot = bot,
        chat_id = call.message.chat.id,
        message_id = call.message.message_id,
        delay = buttons_remove_delay_sec,
      )

      for item in items:
        for item_command in item.get_commands():
          if item_command.command == command:
            item.process_message(fake_message)
            return

      # send message if command not found
      bot.send_message(call.message.chat.id, f"Command '{command}' not found", parse_mode = "HTML")
