import telebot

from telebot_menu_item import TelebotMenuItem
from battery_forecast_utils import BatteryForecastOrderType
from telebot_menu_battery_forecast_base import TelebotMenuBatteryForecastBase

class TelebotMenuBatteryForecastByPercent(TelebotMenuBatteryForecastBase):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(
      bot,
      command = TelebotMenuItem.deye_battery_forecast_by_percent,
      order_type = BatteryForecastOrderType.by_percent,
    )
