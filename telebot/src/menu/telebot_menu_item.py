from enum import Enum
from typing import List

from deye_system_type import DeyeSystemType

class TelebotMenuItem(Enum):
  _command: str
  _description: str
  _system_type: DeyeSystemType

  request_access = ('request_access', 'Request access')
  restart = ('restart', 'Restart bot', DeyeSystemType.none)
  revert = ('revert', 'Revert bot', DeyeSystemType.none)
  update = ('update', 'Update bot', DeyeSystemType.none)

  # if you want to see all commands in Telegram menu,
  # remove system_type parameter or replace it to DeyeSystemType.any
  deye_all_info = ('{0}_info', '{0} info', DeyeSystemType.multi_inverter)
  deye_master_info = ('{0}_info', '{0} info', DeyeSystemType.single_inverter)
  deye_slave_info = ('{0}_info', '{0} info', DeyeSystemType.none)
  deye_all_today_stat = ('{0}_today_stat', '{0} today stat', DeyeSystemType.multi_inverter)
  deye_master_today_stat = ('{0}_today_stat', '{0} today stat', DeyeSystemType.single_inverter)
  deye_slave_today_stat = ('{0}_today_stat', '{0} today stat', DeyeSystemType.none)
  deye_all_total_stat = ('{0}_total_stat', '{0} total stat', DeyeSystemType.multi_inverter)
  deye_master_total_stat = ('{0}_total_stat', '{0} total stat', DeyeSystemType.single_inverter)
  deye_slave_total_stat = ('{0}_total_stat', '{0} total stat', DeyeSystemType.none)
  deye_all_settings = ('{0}_settings', '{0} settings', DeyeSystemType.none)
  deye_master_settings = ('{0}_settings', '{0} settings')
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
    return self.system_type in (DeyeSystemType.any, system_type)

  def __new__(cls, command: str, description: str, system_type: DeyeSystemType = DeyeSystemType.any):
    obj = object.__new__(cls)
    obj._value_ = cls._next_value()
    obj._command = command
    obj._description = description
    obj._system_type = system_type
    return obj

  @classmethod
  def all(cls) -> List['TelebotMenuItem']:
    return list(cls)

  @classmethod
  def _next_value(cls):
    # Collect all existing _value_ attributes of current enum members
    existing = [m._value_ for m in cls.__members__.values()]
    # Return the next integer value: one higher than the current maximum,
    # or 1 if there are no existing members yet
    return max(existing, default = 0) + 1
