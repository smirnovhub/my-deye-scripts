import telebot

from typing import List

from deye_loggers import DeyeLoggers
from telebot_users import TelebotUsers
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item import TelebotMenuItem
from telebot_logging_handler import TelebotLoggingHandler
from telebot_menu_request_access import TelebotMenuRequestAccess
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_menu_all_info import TelebotMenuAllInfo
from telebot_menu_sync_time import TelebotMenuSyncTime
from telebot_menu_master_info import TelebotMenuMasterInfo
from telebot_menu_slave_info import TelebotMenuSlaveInfo
from telebot_menu_all_today_stat import TelebotMenuAllTodayStat
from telebot_menu_all_total_stat import TelebotMenuAllTotalStat
from telebot_menu_slave_today_stat import TelebotMenuSlaveTodayStat
from telebot_menu_slave_total_stat import TelebotMenuSlaveTotalStat
from telebot_menu_master_settings import TelebotMenuMasterSettings
from telebot_menu_battery_forecast import TelebotMenuBatteryForecast
from telebot_menu_writable_registers import TelebotMenuWritableRegisters
from telebot_menu_master_today_stat import TelebotMenuMasterTodayStat
from telebot_menu_master_total_stat import TelebotMenuMasterTotalStat
from telebot_menu_unknown_command_handler import TelebotMenuUnknownCommandHandler
from telebot_user_choices import register_global_handler_for_user_choices
from telebot_user_choices import register_global_handler_for_user_choices
from telebot_run_hidden_command_from_button import register_global_callback_handler_for_hidden_command_from_button
from telebot_run_command_from_button import register_global_callback_handler_for_command_from_button

class MyTelebot:
  def __init__(self, bot: telebot.TeleBot):
    self.bot = bot
    self.users = TelebotUsers()
    self.auth_helper = TelebotAuthHelper()
    self.system_type = DeyeLoggers().system_type

    def print_commands(bot: telebot.TeleBot, scope, label):
      commands = bot.get_my_commands(scope = scope)
      print(f"\n{label} commands:")
      for cmd in commands:
        print(f"  /{cmd.command} – {cmd.description}")

    print_commands(bot, telebot.types.BotCommandScopeDefault(), "Default")
    print_commands(bot, telebot.types.BotCommandScopeAllPrivateChats(), "AllPrivateChats")
    print_commands(bot, telebot.types.BotCommandScopeAllGroupChats(), "AllGroupChats")
    print_commands(bot, telebot.types.BotCommandScopeAllChatAdministrators(), "AllChatAdministrators")

    # Register the global inline button handler for user choices (must be called once at startup)
    register_global_handler_for_user_choices(bot)
    # Register the global inline button handler for executing commands (starts with /) via buttons (must be called once at startup)
    register_global_callback_handler_for_command_from_button(bot)
    # Register the global inline button handler for executing hidden commands (starts with #) via buttons (must be called once at startup)
    register_global_callback_handler_for_hidden_command_from_button(bot, self.get_authorized_menu_items(bot))

    # Logging handler
    logger = TelebotLoggingHandler(bot)
    logger.register_handlers()

    default_menu_items = self.get_default_menu_items(bot)
    authorized_menu_items = self.get_authorized_menu_items(bot)
    authorized_menu_items.extend(self.get_writable_registers_menu_items(bot))

    # unknown command handler should be always last
    authorized_menu_items.append(TelebotMenuUnknownCommandHandler(bot, is_authorized_func = self.is_authorized))

    default_commands = []

    for menu_item in default_menu_items:
      if menu_item.command.is_acceptable(self.system_type):
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
      allowed_menu_items = self.auth_helper.get_allowed_menu_items(user, authorized_menu_items)
      authorized_commands = []
      for menu_item in allowed_menu_items:
        if menu_item.command.is_acceptable(self.system_type):
          commands = menu_item.get_commands()
          for command in commands:
            if self.is_command_allowed(user.id, menu_item.command, command.command):
              authorized_commands.append(command)

      # For test purposes only!

#      if not authorized_commands:
#        authorized_commands = default_commands

      bot.set_my_commands(authorized_commands, scope = telebot.types.BotCommandScopeChat(chat_id = user.id))

  def is_authorized(self, message: telebot.types.Message, item: TelebotMenuItem) -> bool:
    if not self.users.has_user(str(message.from_user.id)):
      self.bot.send_message(message.chat.id, 'User is not authorized')
      return False
    return self.is_item_allowed(message, item)

  def is_item_allowed(self, message: telebot.types.Message, item: TelebotMenuItem) -> bool:
    if not self.auth_helper.is_menu_item_allowed(self.users, str(message.from_user.id), item):
      self.bot.send_message(message.chat.id, 'Command is not allowed for this user')
      return False
    return True

  def is_command_allowed(self, user_id: str, item: TelebotMenuItem, command: str) -> bool:
    if item == TelebotMenuItem.deye_writable_registers:
      if not self.auth_helper.is_writable_register_allowed(self.users, user_id, command):
        return False
    return True

  def get_default_menu_items(self, bot) -> List[TelebotMenuItemHandler]:
    return [
      TelebotMenuRequestAccess(bot),
    ]

  def get_authorized_menu_items(self, bot) -> List[TelebotMenuItemHandler]:
    return [
      TelebotMenuAllInfo(bot, is_authorized_func = self.is_authorized),
      TelebotMenuMasterInfo(bot, is_authorized_func = self.is_authorized),
      TelebotMenuSlaveInfo(bot, is_authorized_func = self.is_authorized),
      TelebotMenuAllTodayStat(bot, is_authorized_func = self.is_authorized),
      TelebotMenuAllTotalStat(bot, is_authorized_func = self.is_authorized),
      TelebotMenuMasterTodayStat(bot, is_authorized_func = self.is_authorized),
      TelebotMenuMasterTotalStat(bot, is_authorized_func = self.is_authorized),
      TelebotMenuSlaveTodayStat(bot, is_authorized_func = self.is_authorized),
      TelebotMenuSlaveTotalStat(bot, is_authorized_func = self.is_authorized),
      TelebotMenuMasterSettings(bot, is_authorized_func = self.is_authorized),
      TelebotMenuBatteryForecast(bot, is_authorized_func = self.is_authorized),
      TelebotMenuSyncTime(bot,
                          is_authorized_func = self.is_authorized,
                          is_writable_register_allowed_func = self.is_command_allowed),
    ]

  def get_writable_registers_menu_items(self, bot) -> List[TelebotMenuItemHandler]:
    return [
      TelebotMenuWritableRegisters(bot,
                                   is_authorized_func = self.is_authorized,
                                   is_writable_register_allowed_func = self.is_command_allowed),
    ]
