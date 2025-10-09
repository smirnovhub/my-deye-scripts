import random

from typing import List

from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from telebot_menu_item import TelebotMenuItem
from telebot_user import TelebotUser
from testable_telebot import TestableTelebot

class TelebotUnauthorizedUserTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    for command in self.get_all_registered_commands():
      user = TelebotUser(
        name = 'Fake user',
        id = random.randint(1000, 9999),
      )

      self.log.info(f"Sending command '/{command}' from user {user.id}")

      self.send_text(user, f'/{command}')

      if command == TelebotMenuItem.request_access.command:
        self.wait_for_text(f'Access requested for user {user.id}')
      else:
        self.wait_for_text(f'User {user.id} is not authorized')

    self.log.info('Seems unauthorized users processed currectly')
    self.log.info(f'Module {type(self).__name__} done successfully')
