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

    self.bot.send_message(message.chat.id, self.get_forecast(), parse_mode = 'HTML')

  def get_forecast(self):
    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      register_creator = lambda prefix: ForecastRegisters(prefix),
      **holder_kwargs,
    )

    try:
      holder.read_registers()
    except Exception as e:
      return str(e)
    finally:
      holder.disconnect()

    try:
      soc = holder.master_registers.battery_soc_register
      current = holder.accumulated_registers.battery_current_register
      power = holder.accumulated_registers.battery_power_register

      result = ''

      result += f'{soc.description}: {soc.value} {soc.suffix}\n'
      result += f'{current.description}: {current.value} {current.suffix}\n'
      result += f'{power.description}: {power.value} {power.suffix}\n'

      if abs(current.value) < 0.1:
        result += '<b>Battery is in idle mode</b>'
        return result

      register = holder.accumulated_registers.charge_forecast_register if current.value < 0 else holder.accumulated_registers.discharge_forecast_register
      val = register.value.strip('"')

      result += f'<b>{val}</b>'
      return result
    except Exception as e:
      return str(e)
