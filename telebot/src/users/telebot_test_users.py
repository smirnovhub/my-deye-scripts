from typing import List

from telebot_user import TelebotUser
from telebot_menu_item import TelebotMenuItem
from telebot_base_users import TelebotBaseUsers

class TelebotTestUsers(TelebotBaseUsers):
  @property
  def test_user1(self) -> TelebotUser:
    return TelebotUser(
      name = 'Andreas Karagiannis',
      id = 1234567,
      # Empty - means all allowed
      allowed_menu_items = [],
      # Empty - means none disabled (all allowed)
      disabled_menu_items = [],
      # Empty - means all allowed
      allowed_writable_registers = [],
      # Empty - means none disabled (all allowed)
      disabled_writable_registers = [],
    )

  @property
  def test_user2(self) -> TelebotUser:
    return TelebotUser(
      name = 'Andreas Karagiannis',
      id = 123123123,
      # Empty - means all allowed
      allowed_menu_items = [
        TelebotMenuItem.deye_all_today_stat,
        TelebotMenuItem.deye_all_total_stat,
        TelebotMenuItem.deye_master_info,
        TelebotMenuItem.deye_slave_info,
      ],
      # Empty - means none disabled (all allowed)
      disabled_menu_items = [
        TelebotMenuItem.deye_all_today_stat,
      ],
      # Empty - means all allowed
      allowed_writable_registers = [],
      # Empty - means none disabled (all allowed)
      disabled_writable_registers = [],
    )

  @property
  def test_user3(self) -> TelebotUser:
    return TelebotUser(
      name = 'Nikos Panagiotopoulos',
      id = 112233,
      # Empty - means all allowed
      allowed_menu_items = [
        TelebotMenuItem.deye_all_info,
        TelebotMenuItem.deye_writable_registers,
        TelebotMenuItem.deye_all_total_stat,
        TelebotMenuItem.deye_slave_today_stat,
        TelebotMenuItem.deye_master_info,
        TelebotMenuItem.deye_slave_info,
        TelebotMenuItem.deye_master_total_stat,
      ],
      # Empty - means none disabled (all allowed)
      disabled_menu_items = [
        TelebotMenuItem.deye_all_total_stat,
        TelebotMenuItem.deye_master_info,
        TelebotMenuItem.deye_slave_info,
      ],
      # Empty - means all allowed
      allowed_writable_registers = [
        self.registers.ac_couple_frz_high_register,
        self.registers.time_of_use_power_register,
        self.registers.grid_peak_shaving_power_register,
        self.registers.zero_export_power_register,
      ],
      # Empty - means none disabled (all allowed)
      disabled_writable_registers = [
        self.registers.ac_couple_frz_high_register,
        self.registers.time_of_use_soc_register,
      ],
    )

  @property
  def blocked_user1(self) -> TelebotUser:
    return TelebotUser(
      name = 'Maria Georgiou',
      id = 7654321,
    )

  @property
  def blocked_user2(self) -> TelebotUser:
    return TelebotUser(
      name = 'Sophia Dimitriadis',
      id = 234235646,
    )

  @property
  def allowed_users(self) -> List[TelebotUser]:
    return [self.test_user1, self.test_user2, self.test_user3, self.blocked_user2]

  @property
  def blocked_users(self) -> List[TelebotUser]:
    return [self.blocked_user1, self.blocked_user2]
