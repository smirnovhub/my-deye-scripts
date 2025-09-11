import sys
from typing import List

from deye_utils import *
from datetime import datetime
from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor

class ChargeForecastRegister(BaseDeyeRegister):
  def __init__(self, battery_soc_register: DeyeRegister,
               battery_capacity_register: DeyeRegister,
               battery_current_register: DeyeRegister,
               name: str, description: str, suffix: str):
    super().__init__(0, 0, name, description, suffix)

    self._battery_soc_register = battery_soc_register
    self._battery_capacity_register = battery_capacity_register
    self._battery_current_register = battery_current_register

  @property
  def type_name(self):
    return 'str'

  @property
  def addresses(self):
    addresses = self._battery_soc_register.addresses +\
      self._battery_capacity_register.addresses +\
      self._battery_current_register.addresses
    return list(set(addresses))

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._battery_soc_register.enqueue(interactor)
    self._battery_capacity_register.enqueue(interactor)
    self._battery_current_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._battery_soc_register.read(interactors)
    self._battery_capacity_register.read(interactors)
    self._battery_current_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    # Charge forecast
    battery_soc = self._battery_soc_register.value
    battery_capacity = self._battery_capacity_register.value
    battery_current = self._battery_current_register.value

    if abs(battery_current) < 0.1:
      value = '"Battery is in idle mode"'
      return value

    if battery_current > 0:
      value = '"Battery is discharging"'
      return value

    percent_step = 5
    charge_lost_coef = 1.16

    soc = battery_soc - battery_soc % percent_step

    if soc >= 100:
      value = '"Battery is fully charged"'
      return value

    value = '"Charge forecast:\n'

    while True:
      soc += percent_step

      if soc > 100:
        break

      if soc <= battery_soc:
        continue

      soc_delta = soc - battery_soc

      # 10% is unused space
      if soc >= 90:
        soc_delta = (90 - battery_soc) + soc_delta * 0.1

      capacity = battery_capacity * (soc_delta / 100) * charge_lost_coef
      hours_to_soc = abs(capacity / battery_current)
      hours_to_soc_str = format_timedelta(timedelta(hours = hours_to_soc))
      soc_date = datetime.now() + timedelta(hours = hours_to_soc)
      soc_date_str = format_end_date(soc_date)

      value += '{:2d}'.format(int(round(soc))) + f'%: {soc_date_str}\n'

    value = value.strip() + '"'

    return value
