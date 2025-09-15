import telebot
from typing import cast

from telebot_fake_message import TelebotFakeMessage

def register_global_callback_handler_for_command_from_button(bot: telebot.TeleBot):
  """
  Registers a global callback handler that will intercept all button clicks.

  If the callback_data starts with '/', it will be interpreted as a bot command
  and executed using process_new_messages().
  Otherwise, the callback will be handled as a normal inline button.
  """
  @bot.callback_query_handler(func = lambda call: call.data and call.data.startswith('/'))
  def handle(call: telebot.types.CallbackQuery):
    if call.data:
      # If callback_data looks like a command (starts with '/'),
      # we create a fake Message object that contains this command.
      fake_message = TelebotFakeMessage(
        cast(telebot.types.Message, call.message),  # original message object
        call.data,  # command text (e.g. "/status")
        call.from_user,  # user who clicked the button
      )

      # Send the fake message into TeleBot's processing pipeline
      # This way, the command handler will process it normally
      bot.process_new_messages([fake_message])
