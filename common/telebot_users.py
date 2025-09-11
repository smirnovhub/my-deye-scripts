from typing import List
from telebot_user import TelebotUser
from telebot_menu_command import TelebotMenuCommand

class TelebotUsers:
  def __init__(self):
    self._users = [
      # ADD AUTHORIZED USERS HERE AND CPECIFY ALLOWED COMMANDS
      # allowed_commands = TelebotMenuCommand.all()
      # will allow all commands
#      TelebotUser(name = 'Dimitras Papandopoulos',
#                  id = '1234567890',
#                  allowed_commands = [
#                    TelebotMenuCommand.deye_master_info,
#                    TelebotMenuCommand.deye_battery_forecast,
#                  ]
#      )
    ]

  @property
  def users(self) -> List[TelebotUser]:
    return self._users.copy()

  def has_user(self, user_id: str) -> bool:
    return any(user.id == str(user_id) for user in self._users)
  
  def get_user(self, user_id: str) -> TelebotUser:
    for user in self._users:
      if user.id == str(user_id):
        return user
    return None

  def get_allowed_commands(self, user_id: str) -> List[TelebotMenuCommand]:
    user = self.get_user(user_id)
    return user.allowed_commands if user else []
  
  def is_command_allowed(self, user_id: str, command: TelebotMenuCommand) -> bool:
    user = self.get_user(user_id)
    return command in user.allowed_commands if user else False
