from telebot_menu_command import TelebotMenuCommand
from telebot_menu_item import TelebotMenuItem

class TelebotMenuUnknownCommandHandler(TelebotMenuItem):
  def __init__(self, bot, is_authorized_func):
    self.bot = bot
    self.is_authorized = is_authorized_func

  @property
  def command(self) -> TelebotMenuCommand:
    return TelebotMenuCommand.unknown_command_echo

  def get_commands(self):
    return []

  def register_handlers(self):
    @self.bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
    def handle(message):
      if not self.is_authorized(message, self.command):
        return

      self.bot.reply_to(message, 'Unknown command')
