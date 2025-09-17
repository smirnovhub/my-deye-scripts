from enum import Enum
from typing import List

from deye_system_type import DeyeSystemType

class TelebotMenuItem(Enum):
  restart = ('restart', 'Restart bot')
  request_access = ('request_access', 'Request access')

  # if you want to see all commands in Telegram menu,
  # remove system_type parameter or replace it to DeyeSystemType.any
  deye_all_info = ('all_info', 'All info', DeyeSystemType.multi_inverter)
  deye_master_info = ('master_info', 'Master info', DeyeSystemType.single_inverter)
  deye_slave_info = ('{0}_info', '{0} info', DeyeSystemType.none)
  deye_all_today_stat = ('all_today_stat', 'All today stat', DeyeSystemType.multi_inverter)
  deye_master_today_stat = ('master_today_stat', 'Master today stat', DeyeSystemType.single_inverter)
  deye_slave_today_stat = ('{0}_today_stat', '{0} today stat', DeyeSystemType.none)
  deye_all_total_stat = ('all_total_stat', 'All total stat', DeyeSystemType.multi_inverter)
  deye_master_total_stat = ('master_total_stat', 'Master total stat', DeyeSystemType.single_inverter)
  deye_slave_total_stat = ('{0}_total_stat', '{0} total stat', DeyeSystemType.none)
  deye_master_settings = ('master_settings', 'Master settings')
  deye_battery_forecast = ('forecast', 'Battery forecast')
  deye_sync_time = ('sync_time', 'Sync inverter time')
  deye_writable_registers = ('{0}', '{0}')

  unknown_command_echo = ('', '')

  unknown = ('', '')

  @property
  def command(self) -> str:
    return self._command

  @property
  def description(self) -> str:
    return self._description

  @property
  def system_type(self) -> DeyeSystemType:
    return self._system_type

  def is_acceptable(self, system_type: DeyeSystemType) -> bool:
    return self.system_type == DeyeSystemType.any or self.system_type == system_type

  def __new__(cls, command: str, description: str, system_type: DeyeSystemType = DeyeSystemType.any):
    obj = object.__new__(cls)
    obj._value_ = command
    obj._command = command
    obj._description = description
    obj._system_type = system_type
    return obj

  @classmethod
  def all(cls) -> List['TelebotMenuItem']:
    return list(cls)
