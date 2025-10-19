import random

from typing import List

from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from telebot_menu_item import TelebotMenuItem
from telebot_user import TelebotUser
from testable_telebot import TestableTelebot

class TelebotUnauthorizedUserTestModule(TelebotBaseTestModule):
  """
  Module `TelebotUnauthorizedUserTestModule` verifies how the Telegram bot
  handles commands from **unauthorized users**.

  The goal is to confirm that all commands either trigger an access request or
  produce a clear "not authorized" message.

  **Test flow:**
  - Iterates through all registered bot commands.  
  - Simulates a random fake user without access rights.  
  - Sends each command to the bot.  
  - Checks responses:
    - Access request command → bot confirms the access request.  
    - Any other command → bot responds that the user is not authorized.  

  This module ensures unauthorized users cannot execute commands and that
  access requests are handled correctly.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'unauthorized user test'

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    for command in self.get_all_registered_commands():
      user = TelebotUser(
        name = 'Fake user',
        id = random.randint(1000, 9999),
      )

      self.log.info(f"Sending command '/{command}' from user {user.id}")

      self.send_text(user, f'/{command}')

      if command == TelebotMenuItem.start.command:
        self.wait_for_text(f'Access requested for user {user.id}')
      else:
        self.wait_for_text(f'User {user.id} is not authorized')

    self.log.info('Seems unauthorized users processed correctly')
