import telebot

from typing import Dict

from deye_utils import DeyeUtils
from deye_registers_holder import DeyeRegistersHolder
from forecast_registers import ForecastRegisters
from telebot_command_choice import CommandChoice
from telebot_deye_helper import TelebotDeyeHelper
from telebot_menu_item import TelebotMenuItem
from telebot_menu_item_handler import TelebotMenuItemHandler
from battery_forecast_utils import BatteryForecastUtils
from battery_forecast_utils import BatteryForecastType
from battery_forecast_utils import BatteryForecastOrderType

class TelebotMenuBatteryForecastBase(TelebotMenuItemHandler):
  def __init__(
    self,
    bot: telebot.TeleBot,
    command: TelebotMenuItem,
    order_type: BatteryForecastOrderType,
  ):
    super().__init__(bot)
    self.cmd = command
    self.order_type = order_type

  @property
  def command(self) -> TelebotMenuItem:
    return self.cmd

  def process_message(self, message: telebot.types.Message):
    if not self.is_authorized(message):
      return

    if self.has_updates(message):
      return

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = self.loggers.loggers,
      register_creator = lambda prefix: ForecastRegisters(prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.read_registers()
    except Exception as e:
      self.bot.send_message(message.chat.id, str(e))
      return
    finally:
      holder.disconnect()

    try:
      result = f'<b>Inverter: {self.loggers.accumulated_registers_prefix}</b>\n'
      result += TelebotDeyeHelper.get_register_values(holder.accumulated_registers.all_registers)

      if self.order_type == BatteryForecastOrderType.by_percent:
        forecast = BatteryForecastUtils.get_forecast_by_percent(
          battery_capacity = holder.master_registers.battery_capacity_register.value,
          battery_soc = holder.master_registers.battery_soc_register.value,
          battery_current = holder.accumulated_registers.battery_current_register.value,
        )
      else:
        forecast = BatteryForecastUtils.get_forecast_by_time(
          battery_capacity = holder.master_registers.battery_capacity_register.value,
          battery_soc = holder.master_registers.battery_soc_register.value,
          battery_current = holder.accumulated_registers.battery_current_register.value,
        )

      if forecast.type == BatteryForecastType.charge:
        result += '<b>Charge forecast:</b>\n'
      else:
        result += '<b>Discharge forecast:</b>\n'

      for item in forecast.items:
        soc_date_str = DeyeUtils.format_end_date(item.date)
        result += f'{item.soc}%: {soc_date_str}\n'

      choices: Dict[str, str] = {}

      if self.auth_helper.is_menu_item_allowed(message.from_user.id, TelebotMenuItem.deye_battery_forecast_by_percent):
        choices['By percent'] = f'/{TelebotMenuItem.deye_battery_forecast_by_percent.command}'

      if self.auth_helper.is_menu_item_allowed(message.from_user.id, TelebotMenuItem.deye_battery_forecast_by_time):
        choices['By time'] = f'/{TelebotMenuItem.deye_battery_forecast_by_time.command}'

      CommandChoice.ask_command_choice(
        self.bot,
        message.chat.id,
        result,
        choices,
        max_per_row = 2,
      )
    except Exception as e:
      self.bot.send_message(message.chat.id, f'{result}{str(e)}', parse_mode = 'HTML')
