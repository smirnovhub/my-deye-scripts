import telebot

from telebot.async_telebot import AsyncTeleBot

from time_of_use_data_holder import TimeOfUseDataHolder
from time_of_use_helper import TimeOfUseHelper
from time_of_use_page_type import TimeOfUsePageType
from time_of_use_enable_page import TimeOfUseEnablePage
from time_of_use_hours_page import TimeOfUseHoursPage
from time_of_use_main_page import TimeOfUseMainPage
from time_of_use_edit_page import TimeOfUseEditPage
from time_of_use_minutes_page import TimeOfUseMinutesPage
from time_of_use_powers_page import TimeOfUsePowersPage
from time_of_use_socs_page import TimeOfUseSocsPage
from telebot_page_navigator import TelebotPageNavigator
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync
from time_of_use_undo_page import TimeOfUseUndoPage

class TelebotMenuTimeOfUse(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: AsyncTeleBot,
  ):
    super().__init__(bot)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_time_of_use

  async def process_message(self, message: telebot.types.Message) -> None:
    tou_registers = await TimeOfUseHelper.read_time_of_use()
    tou_register = tou_registers.time_of_use_register
    tou_data = TimeOfUseHelper.get_time_of_use_data(tou_registers)

    battery_low_batt_soc_register = tou_registers.battery_low_batt_soc_register

    navigator = TelebotPageNavigator(self.bot)
    tou_data_holder = TimeOfUseDataHolder(tou_data)

    enable_page = TimeOfUseEnablePage(
      tou_register = tou_register,
      tou_data_holder = tou_data_holder,
    )

    main_page = TimeOfUseMainPage(tou_data_holder)

    navigator.register_pages([
      enable_page,
      main_page,
      TimeOfUseEditPage(
        tou_register = tou_register,
        tou_data_holder = tou_data_holder,
      ),
      TimeOfUseHoursPage(
        title = "Start hour:",
        tou_data_holder = tou_data_holder,
        page_type = TimeOfUsePageType.start_hours,
        next_page_type = TimeOfUsePageType.start_minutes,
      ),
      TimeOfUseMinutesPage(
        title = "Start minute:",
        tou_data_holder = tou_data_holder,
        page_type = TimeOfUsePageType.start_minutes,
        prev_page_type = TimeOfUsePageType.start_hours,
      ),
      TimeOfUseHoursPage(
        title = "End hour:",
        tou_data_holder = tou_data_holder,
        page_type = TimeOfUsePageType.end_hours,
        next_page_type = TimeOfUsePageType.end_minutes,
      ),
      TimeOfUseMinutesPage(
        title = "End minute:",
        tou_data_holder = tou_data_holder,
        page_type = TimeOfUsePageType.end_minutes,
        prev_page_type = TimeOfUsePageType.end_hours,
      ),
      TimeOfUsePowersPage(tou_data_holder),
      TimeOfUseSocsPage(
        tou_data_holder = tou_data_holder,
        minimum_soc = battery_low_batt_soc_register.value - 1,
      ),
      TimeOfUseUndoPage(
        tou_register = tou_register,
        tou_data_holder = tou_data_holder,
      ),
    ])

    if tou_data.week.enabled:
      await navigator.start(
        page = main_page,
        chat_id = message.chat.id,
      )
    else:
      await navigator.start(
        page = enable_page,
        chat_id = message.chat.id,
      )
