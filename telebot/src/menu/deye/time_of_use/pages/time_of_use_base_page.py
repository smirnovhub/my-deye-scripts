import copy

from dataclasses import asdict

from common_utils import CommonUtils
from custom_single_registers import CustomSingleRegisters
from telebot_deye_helper import TelebotDeyeHelper
from time_of_use_data import TimeOfUseData
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from deye_registers_holder import DeyeRegistersHolder
from telebot_navigation_page import TelebotNavigationPage

class TimeOfUseBasePage(TelebotNavigationPage):
  def __init__(self):
    super().__init__()
    self._loggers = DeyeLoggers()
    registers = DeyeRegisters()
    self._register = registers.time_of_use_register

  def get_time_of_use_as_text(self, data: TimeOfUseData) -> str:
    def sign(value: bool):
      on = CommonUtils.large_green_circle_emoji
      off = CommonUtils.large_red_circle_emoji
      return on if value else off

    weekly = data.weeks.values[0]

    header = f'{sign(weekly.enabled)} Time of Use schedule:'
    schedule = 'Gr Gen    Time     Pwr SOC\n'

    charges = data.charges.values
    times = data.times.values
    powers = data.powers.values
    socs = data.socs.values

    count = len(times)
    for i in range(count):
      curr_charge = charges[i]
      curr_time = times[i]
      # Next time for the interval end, wrapping around to the first element
      next_time = times[(i + 1) % count]
      curr_power = powers[i]
      curr_soc = socs[i]

      schedule += (f'{sign(curr_charge.grid_charge)} {sign(curr_charge.gen_charge)} '
                   f'{curr_time.hour:02d}:{curr_time.minute:02d} '
                   f'{next_time.hour:02d}:{next_time.minute:02d} '
                   f'{curr_power:>4} {curr_soc:>3}\n')

    days_of_week = 'Mon Tue Wed Thu Fri Sat Sun\n'
    days_of_week += (f'{sign(weekly.monday)}  '
                     f'{sign(weekly.tuesday)}  '
                     f'{sign(weekly.wednesday)}  '
                     f'{sign(weekly.thursday)}  '
                     f'{sign(weekly.friday)}  '
                     f'{sign(weekly.saturday)}  '
                     f'{sign(weekly.sunday)}')

    return f'{header}\n<pre>{days_of_week}</pre>\n<pre>{schedule}</pre>'

  def write_time_of_use(
    self,
    tou_data: TimeOfUseData,
    tou_original_data: TimeOfUseData,
  ) -> None:
    if asdict(tou_data) == asdict(tou_original_data):
      return

    data = copy.deepcopy(tou_data)

    self.clear_unchanged_data(
      data_to_clear = data,
      original_data = tou_original_data,
    )

    # should be local to avoid issues with locks
    holder = DeyeRegistersHolder(
      loggers = [self._loggers.master],
      register_creator = lambda prefix: CustomSingleRegisters(self._register, prefix),
      **TelebotDeyeHelper.holder_kwargs,
    )

    try:
      holder.write_register(self._register, data)
    finally:
      holder.disconnect()

  def clear_unchanged_data(
    self,
    data_to_clear: TimeOfUseData,
    original_data: TimeOfUseData,
  ):
    # Convert parts to dicts for simple comparison
    # Use asdict to compare the entire content, not object references
    if asdict(data_to_clear.charges) == asdict(original_data.charges):
      data_to_clear.charges.values = []

    if asdict(data_to_clear.times) == asdict(original_data.times):
      data_to_clear.times.values = []

    if asdict(data_to_clear.powers) == asdict(original_data.powers):
      data_to_clear.powers.values = []

    if asdict(data_to_clear.socs) == asdict(original_data.socs):
      data_to_clear.socs.values = []

    if asdict(data_to_clear.weeks) == asdict(original_data.weeks):
      data_to_clear.weeks.values = []
