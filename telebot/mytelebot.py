import telebot

from telebot_menu_command import TelebotMenuCommand
from telebot_menu_master_info import TelebotMenuMasterInfo
from telebot_menu_slave_info import TelebotMenuSlaveInfo
from telebot_menu_all_info import TelebotMenuAllInfo
from telebot_menu_master_settings import TelebotMenuMasterSettings
from telebot_menu_battery_forecast import TelebotMenuBatteryForecast
from telebot_menu_writeble_registers import TelebotMenuWritebleRegisters
from telebot_menu_unknown_command_handler import TelebotMenuUnknownCommandHandler
from telebot_logging_handler import TelebotLoggingHandler
from telebot_menu_request_access import TelebotMenuRequestAccess
from telebot_users import TelebotUsers

class MyTelebot:
  def __init__(self, bot: telebot.TeleBot):
    self.bot = bot
    self.users = TelebotUsers()

    default_menu_items = [
      TelebotMenuRequestAccess(bot),
    ]

    authorized_menu_items = [
      TelebotMenuAllInfo(bot, is_authorized_func = self.is_authorized),
      TelebotMenuMasterInfo(bot, is_authorized_func = self.is_authorized),
      TelebotMenuSlaveInfo(bot, is_authorized_func = self.is_authorized),
      TelebotMenuMasterSettings(bot, is_authorized_func = self.is_authorized),
      TelebotMenuBatteryForecast(bot, is_authorized_func = self.is_authorized),
      TelebotMenuWritebleRegisters(bot, is_authorized_func = self.is_authorized),
      TelebotMenuUnknownCommandHandler(bot, is_authorized_func = self.is_authorized),
    ]

    def print_commands(bot: telebot.TeleBot, scope, label):
      commands = bot.get_my_commands(scope = scope)
      print(f"\n{label} commands:")
      for cmd in commands:
        print(f"  /{cmd.command} – {cmd.description}")

    print_commands(bot, telebot.types.BotCommandScopeDefault(), "Default")
    print_commands(bot, telebot.types.BotCommandScopeAllPrivateChats(), "AllPrivateChats")
    print_commands(bot, telebot.types.BotCommandScopeAllGroupChats(), "AllGroupChats")
    print_commands(bot, telebot.types.BotCommandScopeAllChatAdministrators(), "AllChatAdministrators")

    # Logging handler
    logger = TelebotLoggingHandler(bot)
    logger.register_handlers()

    default_commands = []

    for menu_item in default_menu_items:
      default_commands.extend(menu_item.get_commands())
      menu_item.register_handlers()

    for menu_item in authorized_menu_items:
      menu_item.register_handlers()

    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeDefault())
    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllPrivateChats())
    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllGroupChats())
    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllChatAdministrators())

    bot.set_chat_menu_button(menu_button = telebot.types.MenuButtonCommands('commands'))

    for user in self.users.users:
      allowed_menu_items = user.get_allowed_menu_items(authorized_menu_items)

      authorized_commands = []
      for menu_item in allowed_menu_items:
        authorized_commands.extend(menu_item.get_commands())

      # For test purposes only!
#      if not authorized_commands:
#        authorized_commands = default_commands

      bot.set_my_commands(
        authorized_commands,
        scope = telebot.types.BotCommandScopeChat(chat_id = user.id)
      )

  def is_authorized(self, message, command: TelebotMenuCommand) -> bool:
    if not self.users.has_user(message.from_user.id):
      self.bot.send_message(message.chat.id, 'User is not authorized')
      return False
    
    if not self.users.is_command_allowed(message.from_user.id, command):
      self.bot.send_message(message.chat.id, 'Command is not allowed for this user')
      return False
    
    return True
