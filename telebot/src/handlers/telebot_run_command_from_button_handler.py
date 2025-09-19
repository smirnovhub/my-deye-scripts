import telebot
from typing import cast

from telebot_fake_message import TelebotFakeMessage
from telebot_base_handler import TelebotBaseHandler

from telebot_constants import buttons_remove_delay_sec
from telebot_utils import remove_inline_buttons_with_delay

class TelebotRunCommandFromButtonHandler(TelebotBaseHandler):
  def __init__(self, bot: telebot.TeleBot):
    self.bot: telebot.TeleBot = bot

  def register_handlers(self):
    """
    Registers a global callback handler that will intercept all button clicks.

    If the callback_data starts with '/', it will be interpreted as a bot command
    and executed using process_new_messages().
    Otherwise, the callback will be handled as a normal inline button.
    """
    @self.bot.callback_query_handler(func = lambda call: call.data and call.data.startswith('/'))
    def handle(call: telebot.types.CallbackQuery):
      if call.data:
        # If callback_data looks like a command (starts with '/'),
        # we create a fake Message object that contains this command.
        fake_message = TelebotFakeMessage(
          cast(telebot.types.Message, call.message), # original message object
          call.data, # command text (e.g. "/status")
          call.from_user, # user who clicked the button
        )

        self.bot.answer_callback_query(call.id)

        remove_inline_buttons_with_delay(
          bot = self.bot,
          chat_id = call.message.chat.id,
          message_id = call.message.message_id,
          delay = buttons_remove_delay_sec,
        )

        # Send the fake message into TeleBot's processing pipeline
        # This way, the command handler will process it normally
        self.bot.process_new_messages([fake_message])
