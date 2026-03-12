import telebot

from common_utils import CommonUtils
from telebot_deye_helper import TelebotDeyeHelper
from time_of_use_data import TimeOfUseData
from custom_single_registers import CustomSingleRegisters
from telebot_menu_item import TelebotMenuItem
from deye_registers_holder import DeyeRegistersHolder
from deye_registers import DeyeRegisters
from telebot_menu_item_handler import TelebotMenuItemHandler

class TelebotMenuTimeOfUse(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.registers = DeyeRegisters()
    self.register = self.registers.time_of_use_register

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_time_of_use

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(self.register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    data = self.register.value

    if not isinstance(data, TimeOfUseData):
      self.bot.send_message(
        message.chat.id,
        f'Register type is not {TimeOfUseData.__name__}',
        parse_mode = 'HTML',
      )
      return

    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    header = f'{sign(data.enabled)} Time of Use schedule:\n'
    schedule = 'Gr Gen    Time     Pwr SOC\n'

    for i in range(0, len(data.items)):
      curr = data.items[i]
      next = data.items[(i + 1) % len(data.items)]
      schedule += (f'{sign(curr.grid_charge)} {sign(curr.gen_charge)} '
                   f'{curr.time.hour:02d}:{curr.time.minute:02d} '
                   f'{next.time.hour:02d}:{next.time.minute:02d} {curr.power:>4} {curr.soc:>3}\n')

    days_of_week = 'Mon Tue Wed Thu Fri Sat Sun\n'
    days_of_week += (f'{sign(data.weekly.monday)}  '
                     f'{sign(data.weekly.tuesday)}  '
                     f'{sign(data.weekly.wednesday)}  '
                     f'{sign(data.weekly.thursday)}  '
                     f'{sign(data.weekly.friday)}  '
                     f'{sign(data.weekly.saturday)}  '
                     f'{sign(data.weekly.sunday)}')

    self.bot.send_message(
      message.chat.id,
      f'{header}<pre>{schedule}</pre>\n<pre>{days_of_week}</pre>',
      parse_mode = 'HTML',
    )
