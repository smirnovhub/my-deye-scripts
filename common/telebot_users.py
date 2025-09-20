from typing import List

from telebot_user import TelebotUser
from telebot_menu_item import TelebotMenuItem
from telebot_base_users import TelebotBaseUsers
from deye_registers_factory import DeyeRegistersFactory

class TelebotUsers(TelebotBaseUsers):
  def __init__(self):
    self.registers = DeyeRegistersFactory.create_registers()

  @property
  def allowed_users(self) -> List[TelebotUser]:
    return [
      # ADD AUTHORIZED USERS HERE AND CPECIFY ALLOWED COMMANDS
      # allowed_commands = TelebotMenuItem.all()
      # will allow all commands
      TelebotUser(
        name = 'Dimitras Papandopoulos',
        id = 1234567890,
        allowed_menu_items = [
          # TelebotMenuItem.deye_all_info,
          # TelebotMenuItem.deye_writable_registers,
          # TelebotMenuItem.deye_all_total_stat,
          # TelebotMenuItem.deye_master_info,
          # TelebotMenuItem.deye_slave_info,
          # TelebotMenuItem.deye_all_today_stat,
        ],
        disabled_menu_items = [
          # TelebotMenuItem.deye_slave_info,
        ],
        allowed_writable_registers = [
          # self.registers.ac_couple_frz_high_register,
          # self.registers.time_of_use_power_register,
          # self.registers.grid_peak_shaving_power_register,
          # self.registers.time_of_use_power_register,
          # self.registers.zero_export_power_register,
        ],
        disabled_writable_registers = [
          # self.registers.ac_couple_frz_high_register,
          # self.registers.time_of_use_power_register,
        ],
      ),
    ]

  @property
  def blocked_users(self) -> List[TelebotUser]:
    return [
      #TelebotUser(
      #  name = 'Dimitras Papandopoulos',
      #  id = 1234567890,
      #),
    ]
