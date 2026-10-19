import asyncio
import logging
import telebot

from telebot.async_telebot import AsyncTeleBot

from typing import List

from telebot_utils import TelebotUtils
from deye_utils import DeyeUtils
from env_utils import EnvUtils
from teletest import TeleTest
from testable_telebot import TestableTelebot
from deye_loggers import DeyeLoggers
from telebot_menu_time_of_use import TelebotMenuTimeOfUse
from telebot_users import TelebotUsers
from telebot_base_handler import TelebotBaseHandler
from telebot_auth_helper import TelebotAuthHelper
from telebot_menu_item import TelebotMenuItem
from telebot_logging_handler import TelebotLoggingHandler
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_menu_all_info import TelebotMenuAllInfo
from telebot_menu_graphs import TelebotMenuGraphs
from telebot_menu_sync_time import TelebotMenuSyncTime
from telebot_menu_restart import TelebotMenuRestart
from telebot_menu_master_info import TelebotMenuMasterInfo
from telebot_menu_slave_info import TelebotMenuSlaveInfo
from telebot_menu_all_today_stat import TelebotMenuAllTodayStat
from telebot_menu_all_total_stat import TelebotMenuAllTotalStat
from telebot_menu_slave_today_stat import TelebotMenuSlaveTodayStat
from telebot_menu_slave_total_stat import TelebotMenuSlaveTotalStat
from telebot_menu_all_settings import TelebotMenuAllSettings
from telebot_menu_master_settings import TelebotMenuMasterSettings
from telebot_menu_battery_forecast import TelebotMenuBatteryForecast
from telebot_menu_writable_registers import TelebotMenuWritableRegisters
from telebot_menu_master_today_stat import TelebotMenuMasterTodayStat
from telebot_menu_master_total_stat import TelebotMenuMasterTotalStat
from telebot_menu_cache import TelebotMenuCache
from telebot_menu_revert import TelebotMenuRevert
from telebot_menu_update import TelebotMenuUpdate
from telebot_menu_test import TelebotMenuTest
from telebot_local_update_checker_async import TelebotLocalUpdateCheckerAsync
from telebot_menu_battery_settings import TelebotMenuBatterySettings
from telebot_menu_battery_forecast_by_percent import TelebotMenuBatteryForecastByPercent
from telebot_menu_battery_forecast_by_time import TelebotMenuBatteryForecastByTime
from telebot_menu_unknown_command_handler import TelebotMenuUnknownCommandHandler
from telebot_run_command_from_button_handler import TelebotRunCommandFromButtonHandler
from telegram_send_message_async import TelegramAsync

class MyTelebot:
  def __init__(
    self,
    bot: AsyncTeleBot,
    logger: logging.Logger,
  ):
    self.bot = bot
    self.users = TelebotUsers()
    self.loggers = DeyeLoggers()
    self.auth_helper = TelebotAuthHelper()
    self.update_checker = TelebotLocalUpdateCheckerAsync()
    self.logger = logger
    self.admin_user_id = EnvUtils.get_telegram_admin_user_id()

  async def initialize(self):
    # # Launch the monitoring task in the background loop
    # asyncio.create_task(TelebotUtils.monitor_hanging_tasks(10))

    data_dir = TelebotUtils.get_data_dir()
    DeyeUtils.ensure_dir_exists(data_dir)

    async def print_commands(scope: telebot.types.BotCommandScope, label: str):
      commands = await self.bot.get_my_commands(scope = scope, language_code = None)
      self.logger.info(f"{label} commands:")
      for cmd in commands:
        self.logger.info(f"  /{cmd.command} - {cmd.description}")

    await print_commands(telebot.types.BotCommandScopeDefault(), "Default")
    await print_commands(telebot.types.BotCommandScopeAllPrivateChats(), "AllPrivateChats")
    await print_commands(telebot.types.BotCommandScopeAllGroupChats(), "AllGroupChats")
    await print_commands(telebot.types.BotCommandScopeAllChatAdministrators(), "AllChatAdministrators")

    try:
      # Save the current commit hash when the bot starts
      # This ensures that future checks can detect local repository changes
      await self.update_checker.update_last_commit_hash()
    except Exception as e:
      message = f'Error while updating last commit hash: {str(e)}'
      self.logger.info(message)
      await TelegramAsync.send_private_telegram_message(message)

    # Register common handlers
    for handler in self.get_common_handlers(self.bot):
      handler.register_handlers()

    default_menu_items = self.get_default_menu_items(self.bot)
    authorized_menu_items = self.get_authorized_menu_items(self.bot)
    authorized_menu_items.extend(self.get_writable_registers_menu_items(self.bot))

    # unknown command handler should be always last
    authorized_menu_items.append(TelebotMenuUnknownCommandHandler(self.bot))

    default_commands: List[telebot.types.BotCommand] = []

    for menu_item in default_menu_items:
      if menu_item.command.is_acceptable(self.loggers.system_type):
        default_commands.extend(menu_item.get_commands())
      menu_item.register_handlers()

    for menu_item in authorized_menu_items:
      menu_item.register_handlers()

    await self.bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeDefault())
    await self.bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllPrivateChats())
    await self.bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllGroupChats())
    await self.bot.set_my_commands(default_commands, scope = telebot.types.BotCommandScopeAllChatAdministrators())
    await self.bot.set_chat_menu_button(menu_button = telebot.types.MenuButtonCommands())

    # Add all commands for admin user
    admin_commands: List[telebot.types.BotCommand] = []
    for menu_item in authorized_menu_items:
      if menu_item.command.is_acceptable(self.loggers.system_type):
        cmds = menu_item.get_commands()
        for command in cmds:
          admin_commands.append(command)

    try:
      await self.bot.set_my_commands(admin_commands,
                                     scope = telebot.types.BotCommandScopeChat(chat_id = self.admin_user_id))
    except Exception as e:
      self.logger.info(f'An exception occurred while setting commands for user {self.admin_user_id}: {str(e)}')

    for user in self.users.allowed_users:
      if user.id == self.admin_user_id:
        # We already set commands for admin user
        continue

      if self.users.is_user_blocked(user.id):
        continue

      authorized_commands: List[telebot.types.BotCommand] = []
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
        await self.bot.set_my_commands(authorized_commands,
                                       scope = telebot.types.BotCommandScopeChat(chat_id = user.id))
      except Exception as e:
        self.logger.info(f'An exception occurred while setting commands for user {user.id}: {str(e)}')

    for user in self.users.blocked_users:
      if user.id == self.admin_user_id:
        # We can't block admin user
        continue

      try:
        await self.bot.set_my_commands([], scope = telebot.types.BotCommandScopeChat(chat_id = user.id))
      except Exception as e:
        self.logger.info(f'An exception occurred while setting command for blocked user {user.id}: {str(e)}')

  def get_common_handlers(self, bot: AsyncTeleBot) -> List[TelebotBaseHandler]:
    return [
      TelebotLoggingHandler(bot),
      TelebotRunCommandFromButtonHandler(bot),
    ]

  def get_default_menu_items(self, bot: AsyncTeleBot) -> List[TelebotMenuItemHandler]:
    return []

  def get_authorized_menu_items(
    self,
    bot: AsyncTeleBot,
  ) -> List[TelebotMenuItemHandler]:
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
      TelebotMenuAllSettings(bot),
      TelebotMenuMasterSettings(bot),
      TelebotMenuGraphs(bot),
      TelebotMenuTimeOfUse(bot),
      TelebotMenuBatterySettings(bot),
      TelebotMenuBatteryForecast(bot),
      TelebotMenuBatteryForecastByPercent(bot),
      TelebotMenuBatteryForecastByTime(bot),
      TelebotMenuSyncTime(bot),
      TelebotMenuRestart(bot),
      TelebotMenuRevert(bot),
      TelebotMenuCache(bot),
      TelebotMenuUpdate(bot),
      TelebotMenuTest(bot),
    ]

  def get_writable_registers_menu_items(
    self,
    bot: AsyncTeleBot,
  ) -> List[TelebotMenuItemHandler]:
    return [
      TelebotMenuWritableRegisters(bot),
    ]

  async def run_tests(self):
    if not isinstance(self.bot, TestableTelebot):
      raise TypeError(f"Can't run tests because telebot is not {TestableTelebot.__name__}")

    teletest = TeleTest(self.bot)
    await teletest.run_tests()
