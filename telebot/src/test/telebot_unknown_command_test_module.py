import random
import string

from typing import List

from telebot_test_users import TelebotTestUsers
from solarman_server import SolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule
from testable_telebot import TestableTelebot

class TelebotUnknownCommandTestModule(TelebotBaseTestModule):
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  def run_tests(self, servers: List[SolarmanServer]):
    user = TelebotTestUsers().test_user1

    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    self.log.info(f'Running module {type(self).__name__}...')

    for i in range(3):
      command = ''.join(random.choices(string.ascii_letters + string.digits, k = 16))

      self.log.info(f"Sending command '/{command}'")

      change_message = TelebotFakeTestMessage.make(
        text = f'/{command}',
        user_id = user.id,
        first_name = user.name,
      )

      self.bot.process_new_messages([change_message])
      self.call_with_retry(self._check_result, command)

    self.log.info('Seems unknown commands processed currectly')

  def _check_result(self, command: str):
    pattern = rf'.*Unknown command: /.*{command}.*'
    if not self.bot.is_messages_contains_regex(pattern):
      self.error(f"No messages to match pattern '{pattern}'")
    else:
      self.log.info(f'Checking command /{command}... OK')
