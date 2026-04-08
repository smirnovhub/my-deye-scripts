import telebot

from telebot_async_runner import TelebotAsyncRunner
from telebot_page_navigator import TelebotPageNavigator
from telebot_menu_item import TelebotMenuItem
from telebot_deye_helper import TelebotDeyeHelper
from battery_settings_registers import BatterySettingsRegisters
from battery_settings_socs_page import BatterySettingsSocsPage
from battery_settings_main_page import BatterySettingsMainPage
from battery_settings_data import BatterySettingsData
from battery_settings_page import BatterySettingsPage
from deye_registers_holder_async import DeyeRegistersHolderAsync
from telebot_menu_item_handler_async import TelebotMenuItemHandlerAsync

class TelebotMenuBatterySettings(TelebotMenuItemHandlerAsync):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot = bot,
      runner = runner,
    )

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_battery_settings

  async def process_message(self, message: telebot.types.Message) -> None:
    # Should be local to avoid issues with locks and threads
    holder = DeyeRegistersHolderAsync(
      loggers = [self.loggers.master],
      register_creator = lambda prefix: BatterySettingsRegisters(prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      await holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    registers = holder.master_registers

    navigator = TelebotPageNavigator(self.bot)

    batt_data = BatterySettingsData(
      values = {
        BatterySettingsPage.shutdown_soc: registers.battery_shutdown_soc_register.value,
        BatterySettingsPage.low_batt_soc: registers.battery_low_batt_soc_register.value,
        BatterySettingsPage.restart_soc: registers.battery_restart_soc_register.value,
      },
      registers = {
        BatterySettingsPage.shutdown_soc: registers.battery_shutdown_soc_register,
        BatterySettingsPage.low_batt_soc: registers.battery_low_batt_soc_register,
        BatterySettingsPage.restart_soc: registers.battery_restart_soc_register,
      },
    )

    title = "Battery settings:"

    main_page = BatterySettingsMainPage(
      runner = self.runner,
      batt_data = batt_data,
      title = title,
    )

    navigator.register_page(main_page)

    for page_type in batt_data.values.keys():
      navigator.register_page(BatterySettingsSocsPage(
        page_type = page_type,
        batt_data = batt_data,
      ))

    navigator.start(
      page = main_page,
      text = title,
      chat_id = message.chat.id,
    )
