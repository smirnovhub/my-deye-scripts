import random

from typing import List

from solarman_server import SolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule
from telebot_menu_item import TelebotMenuItem
from testable_telebot import TestableTelebot

class TelebotUnauthorizedUserTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    for command in self.get_all_registered_commands():
      self.bot.clear_messages()

      user = random.randint(1000, 9999)

      self.log.info(f"Sending command '/{command}' from user {user}")

      change_message = TelebotFakeTestMessage.make(
        text = f'/{command}',
        user_id = user,
      )

      self.bot.process_new_messages([change_message])
      self.call_with_retry(self._check_result, command, user)

    self.log.info('Seems unknown commands processed currectly')

  def _check_result(self, command: str, user: str):
    if command == TelebotMenuItem.request_access.command:
      pattern = f'Access requested for user {user}'
    else:
      pattern = f'User {user} is not authorized'

    if not self.bot.is_messages_contains(pattern):
      self.error(f"No messages to match pattern '{pattern}'")
    else:
      self.log.info(f'Checking command /{command} for user {user}... OK')
