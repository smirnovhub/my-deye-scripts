from enum import Enum

class TelebotMenuItem(Enum):
  request_access = ('request_access', 'Request access')

  deye_all_info = ('all_info', 'All info')
  deye_master_info = ('master_info', 'Master info')
  deye_slave_info = ('{0}_info', '{0} info')
  deye_master_settings = ('master_settings', 'Master settings')
  deye_battery_forecast = ('forecast', 'Battery forecast')
  deye_writable_registers = ('{0}', '{0}')

  unknown_command_echo = ('', '')

  unknown = ('', '')

  @property
  def command(self) -> str:
    return self._command

  @property
  def description(self) -> str:
    return self._description

  def __new__(cls, command, description):
    obj = object.__new__(cls)
    obj._value_ = command
    obj._command = command
    obj._description = description
    return obj

  @classmethod
  def all(cls):
    return list(cls)
