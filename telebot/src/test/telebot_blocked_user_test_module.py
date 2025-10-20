from typing import List

from solarman_server import SolarmanServer
from telebot_base_test_module import TelebotBaseTestModule
from telebot_menu_item import TelebotMenuItem
from telebot_users import TelebotUsers
from testable_telebot import TestableTelebot

class TelebotBlockedUserTestModule(TelebotBaseTestModule):
  """
  Module `TelebotBlockedUserTestModule` tests how the Telegram bot handles
  commands from **blocked users**.

  The goal is to ensure that blocked users cannot execute any commands
  and receive appropriate notifications.

  **Test flow:**
  - Iterates through all blocked users.  
  - Sends every registered bot command from each blocked user.  
  - Checks responses:
    - Access request command → bot responds that the command is not allowed.  
    - Any other command → bot responds that the user is not authorized.  

  This module confirms that blocked users are prevented from performing
  actions and that the bot handles them consistently.
  """
  def __init__(self, bot: TestableTelebot):
    super().__init__(bot)

  @property
  def description(self) -> str:
    return 'blocked user test'

  def run_tests(self, servers: List[SolarmanServer]):
    if not self.loggers.is_test_loggers:
      self.error('Your loggers are not test loggers')

    users = TelebotUsers().blocked_users

    for user in users:
      for command in self.get_all_registered_commands():
        self.log.info(f"Sending command '/{command}' from user {user.id}")

        self.send_text(user, f'/{command}')

        if command == TelebotMenuItem.start.command:
          self.wait_for_text('Command is not allowed for this user')
        else:
          self.wait_for_text('User is not authorized')

    self.log.info('Seems blocked users processed correctly')
