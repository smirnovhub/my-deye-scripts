import telebot

from telebot_constants import TelebotConstants
from telebot_menu_item import TelebotMenuItem
from telebot_menu_master_base import TelebotMenuMasterBase
from total_stat_registers import TotalStatRegisters
from telebot_async_runner import TelebotAsyncRunner

class TelebotMenuMasterTotalStat(TelebotMenuMasterBase):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
      registers_class = TotalStatRegisters,
      all_command = TelebotMenuItem.deye_all_total_stat,
      master_command = TelebotMenuItem.deye_master_total_stat,
      slave_command = TelebotMenuItem.deye_slave_total_stat,
      title = TelebotConstants.total_stat_title,
    )
