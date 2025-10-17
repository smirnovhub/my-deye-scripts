from typing import List

from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from telebot_menu_item import TelebotMenuItem
from telebot_users import TelebotUsers
from testable_telebot import TestableTelebot

class TelebotBlockedUserTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'blocked user test'

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    users = TelebotUsers().blocked_users

    for user in users:
      for command in self.get_all_registered_commands():
        self.log.info(f"Sending command '/{command}' from user {user.id}")

        self.send_text(user, f'/{command}')

        if command == TelebotMenuItem.request_access.command:
          self.wait_for_text('Command is not allowed for this user')
        else:
          self.wait_for_text('User is not authorized')

    self.log.info('Seems blocked users processed correctly')
    self.log.info(f'Module {type(self).__name__} done successfully')
