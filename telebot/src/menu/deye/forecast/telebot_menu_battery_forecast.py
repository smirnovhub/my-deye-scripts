from telebot.async_telebot import AsyncTeleBot
from telebot_menu_item import TelebotMenuItem
from battery_forecast_utils import BatteryForecastOrderType
from telebot_menu_battery_forecast_base import TelebotMenuBatteryForecastBase

class TelebotMenuBatteryForecast(TelebotMenuBatteryForecastBase):
  def __init__(
    self,
    bot: AsyncTeleBot,
  ):
    super().__init__(
      bot,
      command = TelebotMenuItem.deye_battery_forecast,
      order_type = BatteryForecastOrderType.by_percent,
    )
