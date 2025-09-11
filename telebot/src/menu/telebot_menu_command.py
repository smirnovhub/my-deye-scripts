from enum import Enum, auto

class TelebotMenuCommand(Enum):
  request_access = auto()

  deye_all_info = auto()
  deye_master_info = auto()
  deye_slave1_info = auto()
  deye_master_settings = auto()
  deye_battery_forecast = auto()
  deye_writeble_registers = auto()
  
  unknown_command_echo = auto()

  unknown = auto()

  @classmethod
  def all(cls):
    return list(cls)
