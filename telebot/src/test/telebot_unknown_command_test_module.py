import random
import string

from typing import List

from telebot_test_users import TelebotTestUsers
from solarman_server import SolarmanServer
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

    for i in range(5):
      command = ''.join(random.choices(string.ascii_letters + string.digits, k = 16))

      self.log.info(f"Sending command '/{command}'")

      self.send_text(user, f'/{command}')
      self.wait_for_text_regex(rf'.*Unknown command: /.*{command}.*')

    for i in range(5):
      command = ''.join(random.choices(string.ascii_letters + string.digits, k = 16))
      param = ''.join(random.choices(string.ascii_letters + string.digits, k = 8))

      self.log.info(f"Sending command '/{command} {param}'")

      self.send_text(user, f'/{command} {param}')
      self.wait_for_text_regex(rf'.*Unknown command: /.*{command}.*')

    self.log.info('Seems unknown commands processed currectly')
    self.log.info(f'Module {type(self).__name__} done successfully')
