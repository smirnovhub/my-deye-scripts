from typing import List, Union
from telebot_user import TelebotUser
from telebot_menu_item import TelebotMenuItem
from deye_registers_factory import DeyeRegistersFactory

class TelebotUsers:
  def __init__(self):
    registers = DeyeRegistersFactory.create_registers()
    self._allowed_users = [
      # ADD AUTHORIZED USERS HERE AND CPECIFY ALLOWED COMMANDS
      # allowed_commands = TelebotMenuItem.all()
      # will allow all commands
      #TelebotUser(
        #name = 'Dimitras Papandopoulos',
        #id = 1234567890,
        #allowed_menu_items = [
          # TelebotMenuItem.deye_all_info,
          # TelebotMenuItem.deye_writable_registers,
          # TelebotMenuItem.deye_all_total_stat,
          # TelebotMenuItem.deye_master_info,
          # TelebotMenuItem.deye_slave_info,
          # TelebotMenuItem.deye_all_today_stat,
        #],
        #disabled_menu_items = [
          # TelebotMenuItem.deye_slave_info,
        #],
        #allowed_writable_registers = [
          # registers.ac_couple_frz_high_register,
          # registers.time_of_use_power_register,
          # registers.grid_peak_shaving_power_register,
          # registers.time_of_use_power_register,
          # registers.zero_export_power_register,
        #],
        #disabled_writable_registers = [
          # registers.ac_couple_frz_high_register,
          # registers.time_of_use_power_register,
        #],
      #),
    ]

    self._blocked_users = [
      #TelebotUser(
        #name = 'Dimitras Papandopoulos',
        #id = 1234567890,
      #),
    ]

  @property
  def allowed_users(self) -> List[TelebotUser]:
    return self._allowed_users.copy()

  @property
  def blocked_users(self) -> List[TelebotUser]:
    return self._blocked_users.copy()

  def is_user_allowed(self, user_id: int) -> bool:
    return any(user.id == user_id for user in self._allowed_users)

  def get_allowed_user(self, user_id: int) -> Union[TelebotUser, None]:
    for user in self._allowed_users:
      if user.id == user_id:
        return user
    return None

  def is_user_blocked(self, user_id: int) -> bool:
    return any(user.id == user_id for user in self._blocked_users)
