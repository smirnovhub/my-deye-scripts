import telebot

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from forecast_registers import ForecastRegisters
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from telebot_deye_helper import holder_kwargs

class TelebotMenuBatteryForecast(TelebotMenuItemHandler):
  def __init__(self, bot: telebot.TeleBot):
    super().__init__(bot)
    self.loggers = DeyeLoggers()

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_battery_forecast

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      register_creator = lambda prefix: ForecastRegisters(prefix),
      **holder_kwargs,
    )

    try:
      holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    try:
      soc_register = holder.master_registers.battery_soc_register
      current_register = holder.accumulated_registers.battery_current_register
      power_register = holder.accumulated_registers.battery_power_register

      result = ''

      result += f'{soc_register.description}: {soc_register.pretty_value} {soc_register.suffix}\n'
      result += f'{current_register.description}: {current_register.pretty_value} {current_register.suffix}\n'
      result += f'{power_register.description}: {power_register.pretty_value} {power_register.suffix}\n'

      if abs(current_register.value) < 0.1:
        self.bot.send_message(message.chat.id, '<b>Battery is in idle mode</b>', parse_mode = 'HTML')
        return

      register = holder.accumulated_registers.charge_forecast_register if current_register.value < 0 else holder.accumulated_registers.discharge_forecast_register
      val = register.pretty_value.strip('"')

      result += f'<b>{val}</b>'
      self.bot.send_message(message.chat.id, result, parse_mode = 'HTML')
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
