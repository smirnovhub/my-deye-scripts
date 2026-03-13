import copy
import telebot

from dataclasses import asdict

from common_utils import CommonUtils
from pages.time_of_use_hours_page import TimeOfUseHoursPage
from pages.time_of_use_main_page import TimeOfUseMainPage
from pages.time_of_use_minutes_page import TimeOfUseMinutesPage
from pages.time_of_use_page import TimeOfUsePage
from pages.time_of_use_powers_page import TimeOfUsePowersPage
from pages.time_of_use_socs_page import TimeOfUseSocsPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_menu_item import TelebotMenuItem
from deye_registers import DeyeRegisters
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_deye_helper import TelebotDeyeHelper
from telebot_utils import TelebotUtils
from time_of_use_data import TimeOfUseData
from custom_single_registers import CustomSingleRegisters
from deye_registers_holder import DeyeRegistersHolder

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

    original_data = copy.deepcopy(data)

    main_page = TimeOfUseMainPage(data)

    start_hours_page = TimeOfUseHoursPage(
      tou_times = data.times,
      title = "Start hour:",
      page_type = TimeOfUsePage.start_hours,
      next_page_type = TimeOfUsePage.start_minutes,
    )

    start_minutes_page = TimeOfUseMinutesPage(
      tou_times = data.times,
      title = "Start minute:",
      page_type = TimeOfUsePage.start_minutes,
    )

    end_hours_page = TimeOfUseHoursPage(
      tou_times = data.times,
      title = "End hour:",
      page_type = TimeOfUsePage.end_hours,
      next_page_type = TimeOfUsePage.end_minutes,
    )

    end_minutes_page = TimeOfUseMinutesPage(
      tou_times = data.times,
      title = "End minute:",
      page_type = TimeOfUsePage.end_minutes,
    )

    powers_page = TimeOfUsePowersPage(tou_powers = data.powers)
    socs_page = TimeOfUseSocsPage(tou_socs = data.socs)

    navigator = TelebotPageNavigator(self.bot)
    text = "Time of Use schedule:"

    navigator.register_page(main_page)
    navigator.register_page(start_hours_page)
    navigator.register_page(start_minutes_page)
    navigator.register_page(end_hours_page)
    navigator.register_page(end_minutes_page)
    navigator.register_page(powers_page)
    navigator.register_page(socs_page)

    navigator.start(
      chat_id = message.chat.id,
      text = text,
      page = main_page,
    )

    self.bot.clear_step_handler_by_chat_id(message.chat.id)
    self.bot.register_next_step_handler(
      message,
      self._next_step_handler,
      navigator,
      original_data,
    )

  def _next_step_handler(
    self,
    message: telebot.types.Message,
    navigator: TelebotPageNavigator,
    tou_data: TimeOfUseData,
  ):
    text = self._get_time_of_use_as_text(tou_data)
    navigator.stop(text)

    # If we received new command, process it
    TelebotUtils.forward_next(self.bot, message)

  def _clear_unchanged_data(
    self,
    data: TimeOfUseData,
    original_data: TimeOfUseData,
  ):
    # Convert parts to dicts for simple comparison
    # Use asdict to compare the entire content, not object references
    if asdict(data.charges) == asdict(original_data.charges):
      data.charges.values = []

    if asdict(data.times) == asdict(original_data.times):
      data.times.values = []

    if asdict(data.powers) == asdict(original_data.powers):
      data.powers.values = []

    if asdict(data.socs) == asdict(original_data.socs):
      data.socs.values = []

  def _get_time_of_use_as_text(self, data: TimeOfUseData) -> str:
    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    header = f'{sign(data.weekly.enabled)} Time of Use schedule:\n'
    schedule = 'Gr Gen    Time     Pwr SOC\n'

    charges = data.charges.values
    times = data.times.values
    powers = data.powers.values
    socs = data.socs.values

    count = len(times)
    for i in range(count):
      curr_charge = charges[i]
      curr_time = times[i]
      # Next time for the interval end, wrapping around to the first element
      next_time = times[(i + 1) % count]
      curr_power = powers[i]
      curr_soc = socs[i]

      schedule += (f'{sign(curr_charge.grid_charge)} {sign(curr_charge.gen_charge)} '
                   f'{curr_time.hour:02d}:{curr_time.minute:02d} '
                   f'{next_time.hour:02d}:{next_time.minute:02d} '
                   f'{curr_power:>4} {curr_soc:>3}\n')

    days_of_week = 'Mon Tue Wed Thu Fri Sat Sun\n'
    days_of_week += (f'{sign(data.weekly.monday)}  '
                     f'{sign(data.weekly.tuesday)}  '
                     f'{sign(data.weekly.wednesday)}  '
                     f'{sign(data.weekly.thursday)}  '
                     f'{sign(data.weekly.friday)}  '
                     f'{sign(data.weekly.saturday)}  '
                     f'{sign(data.weekly.sunday)}')

    return f'{header}<pre>{schedule}</pre>\n<pre>{days_of_week}</pre>'
