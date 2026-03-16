import telebot

from time_of_use_enable_page import TimeOfUseEnablePage
from time_of_use_hours_page import TimeOfUseHoursPage
from time_of_use_main_page import TimeOfUseMainPage
from time_of_use_minutes_page import TimeOfUseMinutesPage
from time_of_use_page import TimeOfUsePage
from time_of_use_powers_page import TimeOfUsePowersPage
from time_of_use_socs_page import TimeOfUseSocsPage
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

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_time_of_use

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # Should be local to avoid race conditions with threads
    registers = DeyeRegisters()
    tou_register = registers.time_of_use_register

    # Should be local to avoid issues with locks and threads
    holder = DeyeRegistersHolder(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(tou_register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    tou_data = tou_register.value

    if not isinstance(tou_data, TimeOfUseData):
      self.bot.send_message(
        message.chat.id,
        f"Register value type should be {TimeOfUseData.__name__}, but "
        f"{type(tou_register.value).__name__} received",
      )
      return

    navigator = TelebotPageNavigator(self.bot)

    enable_page = TimeOfUseEnablePage(
      tou_register = tou_register,
      tou_data = tou_data,
    )

    main_page = TimeOfUseMainPage(
      tou_register = tou_register,
      tou_data = tou_data,
    )

    navigator.register_pages([
      enable_page,
      main_page,
      TimeOfUseHoursPage(
        tou_times = tou_data.times,
        title = "Start hour:",
        page_type = TimeOfUsePage.start_hours,
        next_page_type = TimeOfUsePage.start_minutes,
      ),
      TimeOfUseMinutesPage(
        tou_times = tou_data.times,
        title = "Start minute:",
        page_type = TimeOfUsePage.start_minutes,
      ),
      TimeOfUseHoursPage(
        tou_times = tou_data.times,
        title = "End hour:",
        page_type = TimeOfUsePage.end_hours,
        next_page_type = TimeOfUsePage.end_minutes,
      ),
      TimeOfUseMinutesPage(
        tou_times = tou_data.times,
        title = "End minute:",
        page_type = TimeOfUsePage.end_minutes,
      ),
      TimeOfUsePowersPage(tou_powers = tou_data.powers),
      TimeOfUseSocsPage(tou_socs = tou_data.socs),
    ])

    if tou_data.week.enabled:
      navigator.start(
        page = main_page,
        text = "Time of Use schedule:",
        chat_id = message.chat.id,
      )
    else:
      navigator.start(
        page = enable_page,
        text = "Time of Use is disabled",
        chat_id = message.chat.id,
      )
