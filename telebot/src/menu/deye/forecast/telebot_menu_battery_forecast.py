import telebot

from telebot_async_runner import TelebotAsyncRunner
from telebot_menu_item import TelebotMenuItem
from battery_forecast_utils import BatteryForecastOrderType
from telebot_menu_battery_forecast_base import TelebotMenuBatteryForecastBase

class TelebotMenuBatteryForecast(TelebotMenuBatteryForecastBase):
  def __init__(
    self,
    bot: telebot.TeleBot,
    runner: TelebotAsyncRunner,
  ):
    super().__init__(
      bot,
      runner = runner,
      command = TelebotMenuItem.deye_battery_forecast,
      order_type = BatteryForecastOrderType.by_percent,
    )
