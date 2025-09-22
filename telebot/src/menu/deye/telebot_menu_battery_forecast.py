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
    loggers = DeyeLoggers()
    self.holder = DeyeRegistersHolder(loggers = loggers.loggers,
                                      register_creator = lambda prefix: ForecastRegisters(prefix),
                                      **holder_kwargs)

  @property
  def command(self) -> TelebotMenuItem:
    return TelebotMenuItem.deye_battery_forecast

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message.from_user.id, message.chat.id):
      return

    self.bot.send_message(message.chat.id, self.get_forecast(), parse_mode = 'HTML')

  def get_forecast(self):
    try:
      self.holder.connect_and_read()
    except Exception as e:
      return str(e)
    finally:
      self.holder.disconnect()

    try:
      soc = self.holder.master_registers.battery_soc_register
      current = self.holder.accumulated_registers.battery_current_register
      power = self.holder.accumulated_registers.battery_power_register

      result = ''

      result += f'{soc.description}: {soc.value} {soc.suffix}\n'
      result += f'{current.description}: {current.value} {current.suffix}\n'
      result += f'{power.description}: {power.value} {power.suffix}\n'

      if abs(current.value) < 0.1:
        result += '<b>Battery is in idle mode</b>'
        return result

      register = self.holder.accumulated_registers.charge_forecast_register if current.value < 0 else self.holder.accumulated_registers.discharge_forecast_register
      val = register.value.strip('"')

      result += f'<b>{val}</b>'
      return result
    except Exception as e:
      return str(e)
