from typing import List, Union
from telebot_user import TelebotUser
from telebot_menu_item import TelebotMenuItem

class TelebotUsers:
  def __init__(self):
    self._users = [
      # ADD AUTHORIZED USERS HERE AND CPECIFY ALLOWED COMMANDS
      # allowed_commands = TelebotMenuItem.all()
      # will allow all commands
#      TelebotUser(
#        name = 'Dimitras Papandopoulos',
#        id = '1234567890',
#        # empty - means none allowed
#        allowed_menu_items = TelebotMenuItem.all(),
#        # empty - means all allowed
#        allowed_writable_registers = [
#          'ac_couple_frz_high',
#          'ct_ratio',
#          'grid_peak_shaving_power',
#          'time_of_use_power',
#          'zero_export_power'
#        ],
#        # empty - means none disabled (all allowed)
#        disabled_writable_registers = [
#          'ac_couple_frz_high',
#          'time_of_use_power',
#        ],
#      ),
    ]

  @property
  def users(self) -> List[TelebotUser]:
    return self._users.copy()

  def has_user(self, user_id: str) -> bool:
    return any(user.id == str(user_id) for user in self._users)

  def get_user(self, user_id: str) -> Union[TelebotUser, None]:
    for user in self._users:
      if user.id == str(user_id):
        return user
    return None
