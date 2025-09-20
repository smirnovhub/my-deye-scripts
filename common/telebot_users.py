from typing import List

from telebot_user import TelebotUser
from telebot_menu_item import TelebotMenuItem
from telebot_base_users import TelebotBaseUsers
from deye_registers_factory import DeyeRegistersFactory

class TelebotUsers(TelebotBaseUsers):
  registers = DeyeRegistersFactory.create_registers()

  @property
  def allowed_users(self) -> List[TelebotUser]:
    return [
      # ADD AUTHORIZED USERS HERE AND CPECIFY ALLOWED COMMANDS
      TelebotUser(
        name = 'Dimitras Papandopoulos',
        id = 1234567890,
        # Empty - means all allowed
        allowed_menu_items = [
          # TelebotMenuItem.deye_all_info,
          # TelebotMenuItem.deye_writable_registers,
          # TelebotMenuItem.deye_all_total_stat,
          # TelebotMenuItem.deye_master_info,
          # TelebotMenuItem.deye_slave_info,
          # TelebotMenuItem.deye_all_today_stat,
        ],
        # Empty - means none disabled (all allowed)
        disabled_menu_items = [
          # TelebotMenuItem.deye_slave_info,
        ],
        # Empty - means all allowed
        allowed_writable_registers = [
          # TelebotUsers.registers.ac_couple_frz_high_register,
          # TelebotUsers.registers.time_of_use_power_register,
          # TelebotUsers.registers.grid_peak_shaving_power_register,
          # TelebotUsers.registers.time_of_use_power_register,
          # TelebotUsers.registers.zero_export_power_register,
        ],
        # Empty - means none disabled (all allowed)
        disabled_writable_registers = [
          # TelebotUsers.registers.ac_couple_frz_high_register,
          # TelebotUsers.registers.time_of_use_power_register,
        ],
      ),
    ]

  @property
  def blocked_users(self) -> List[TelebotUser]:
    return [
      # TelebotUser(
      #   name = 'Dimitras Papandopoulos',
      #   id = 1234567890,
      # ),
    ]
