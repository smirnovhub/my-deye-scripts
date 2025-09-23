import telebot

from typing import List

from deye_loggers import DeyeLoggers
from telebot_users import TelebotUsers
from telebot_base_handler import TelebotBaseHandler
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item import TelebotMenuItem
from telebot_logging_handler import TelebotLoggingHandler
from telebot_menu_request_access import TelebotMenuRequestAccess
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_menu_all_info import TelebotMenuAllInfo
from telebot_menu_sync_time import TelebotMenuSyncTime
from telebot_menu_restart import TelebotMenuRestart
from telebot_local_update_checker import TelebotLocalUpdateChecker
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
from telebot_menu_update_and_restart import TelebotMenuUpdateAndRestart
from telebot_menu_unknown_command_handler import TelebotMenuUnknownCommandHandler
from telebot_run_command_from_button_handler import TelebotRunCommandFromButtonHandler

class MyTelebot:
  def __init__(self, bot: telebot.TeleBot):
    self.bot = bot
    self.users = TelebotUsers()
    self.loggers = DeyeLoggers()
    self.auth_helper = TelebotAuthHelper()
    self.update_checker = TelebotLocalUpdateChecker()

    def print_commands(bot: telebot.TeleBot, scope, label):
      commands = bot.get_my_commands(scope = scope)
      print(f"\n{label} commands:")
      for cmd in commands:
        print(f"  /{cmd.command} – {cmd.description}")

    print_commands(bot, telebot.types.BotCommandScopeDefault(), "Default")
    print_commands(bot, telebot.types.BotCommandScopeAllPrivateChats(), "AllPrivateChats")
    print_commands(bot, telebot.types.BotCommandScopeAllGroupChats(), "AllGroupChats")
    print_commands(bot, telebot.types.BotCommandScopeAllChatAdministrators(), "AllChatAdministrators")

    try:
      # Save the current commit hash when the bot starts
      # This ensures that future checks can detect local repository changes
      self.update_checker.update_last_commit_hash()
    except Exception as e:
      print(f'Error while updating last commit hash: {str(e)}')

    # Register common handlers
    for handler in self.get_common_handlers(bot):
      handler.register_handlers()

    default_menu_items = self.get_default_menu_items(bot)
    authorized_menu_items = self.get_authorized_menu_items(bot)
    authorized_menu_items.extend(self.get_writable_registers_menu_items(bot))

    # unknown command handler should be always last
    authorized_menu_items.append(TelebotMenuUnknownCommandHandler(bot))

    default_commands = []

    for menu_item in default_menu_items:
      if menu_item.command.is_acceptable(self.loggers.system_type):
        default_commands.extend(menu_item.get_commands())
      menu_item.register_handlers()

    for menu_item in authorized_menu_items:
      menu_item.register_handlers()

    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeDefault())
    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllPrivateChats())
    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllGroupChats())
    bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllChatAdministrators())

    bot.set_chat_menu_button(menu_button = telebot.types.MenuButtonCommands('commands'))

    for user in self.users.allowed_users:
      if self.users.is_user_blocked(user.id):
        continue
      authorized_commands = []
      for menu_item in authorized_menu_items:
        if menu_item.is_item_allowed_for_user(user) and menu_item.command.is_acceptable(self.loggers.system_type):
          commands = menu_item.get_commands()
          for command in commands:
            if menu_item.command != TelebotMenuItem.deye_writable_registers:
              authorized_commands.append(command)
            elif self.auth_helper.is_writable_register_allowed(user.id, command.command):
              authorized_commands.append(command)

      # For test purposes only!
      # if not authorized_commands:
      # authorized_commands = default_commands

      try:
        bot.set_my_commands(authorized_commands, scope = telebot.types.BotCommandScopeChat(chat_id = user.id))
      except Exception as e:
        print(f'An exception occurred while setting commands for user {user.id}: {str(e)}')

    for user in self.users.blocked_users:
      try:
        bot.set_my_commands([], scope = telebot.types.BotCommandScopeChat(chat_id = user.id))
      except Exception as e:
        print(f'An exception occurred while setting command for blocking user {user.id}: {str(e)}')

  def get_common_handlers(self, bot) -> List[TelebotBaseHandler]:
    return [
      TelebotLoggingHandler(bot),
      TelebotRunCommandFromButtonHandler(bot),
    ]

  def get_default_menu_items(self, bot) -> List[TelebotMenuItemHandler]:
    return [
      TelebotMenuRequestAccess(bot),
    ]

  def get_authorized_menu_items(self, bot) -> List[TelebotMenuItemHandler]:
    return [
      TelebotMenuAllInfo(bot),
      TelebotMenuMasterInfo(bot),
      TelebotMenuSlaveInfo(bot),
      TelebotMenuAllTodayStat(bot),
      TelebotMenuAllTotalStat(bot),
      TelebotMenuMasterTodayStat(bot),
      TelebotMenuMasterTotalStat(bot),
      TelebotMenuSlaveTodayStat(bot),
      TelebotMenuSlaveTotalStat(bot),
      TelebotMenuMasterSettings(bot),
      TelebotMenuBatteryForecast(bot),
      TelebotMenuSyncTime(bot),
      TelebotMenuRestart(bot),
      TelebotMenuUpdateAndRestart(bot),
    ]

  def get_writable_registers_menu_items(self, bot) -> List[TelebotMenuItemHandler]:
    return [
      TelebotMenuWritableRegisters(bot),
    ]
