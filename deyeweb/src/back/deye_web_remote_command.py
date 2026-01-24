from enum import Enum, auto

class DeyeWebRemoteCommand(Enum):
  read_registers = auto()
  write_register = auto()
  get_forecast_by_percent = auto()
  get_forecast_by_time = auto()
