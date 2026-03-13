from pages.time_of_use_hours_page import TimeOfUseHoursPage
from pages.time_of_use_main_page import TimeOfUseMainPage
from pages.time_of_use_minutes_page import TimeOfUseMinutesPage
from pages.time_of_use_page import TimeOfUsePage
from pages.time_of_use_powers_page import TimeOfUsePowersPage
from pages.time_of_use_socs_page import TimeOfUseSocsPage
import telebot

from telebot_page_navigator import TelebotPageNavigator
from telebot_menu_item import TelebotMenuItem
from deye_registers import DeyeRegisters
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_deye_helper import TelebotDeyeHelper
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

    if not isinstance(self.register.value, TimeOfUseData):
      self.bot.send_message(
        message.chat.id,
        f'Register type is not {TimeOfUseData.__name__}',
        parse_mode = 'HTML',
      )
      return

    main_page = TimeOfUseMainPage(self.register.value)

    start_hours_page = TimeOfUseHoursPage(
      tou_times = self.register.value.times,
      title = "Start hour:",
      page_type = TimeOfUsePage.start_hours,
      next_page_type = TimeOfUsePage.start_minutes,
    )

    start_minutes_page = TimeOfUseMinutesPage(
      tou_times = self.register.value.times,
      title = "Start minute:",
      page_type = TimeOfUsePage.start_minutes,
    )

    end_hours_page = TimeOfUseHoursPage(
      tou_times = self.register.value.times,
      title = "End hour:",
      page_type = TimeOfUsePage.end_hours,
      next_page_type = TimeOfUsePage.end_minutes,
    )

    end_minutes_page = TimeOfUseMinutesPage(
      tou_times = self.register.value.times,
      title = "End minute:",
      page_type = TimeOfUsePage.end_minutes,
    )

    powers_page = TimeOfUsePowersPage(tou_powers = self.register.value.powers)
    socs_page = TimeOfUseSocsPage(tou_socs = self.register.value.socs)

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
