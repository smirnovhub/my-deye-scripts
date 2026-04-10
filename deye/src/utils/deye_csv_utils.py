from typing import List
from datetime import datetime

from deye_loggers import DeyeLoggers
from deye_registers_holder import DeyeRegistersHolder
from deye_register_average_type import DeyeRegisterAverageType

class DeyeCsvUtils:
  @staticmethod
  def get_csv_header() -> str:
    return "timestamp,inverter,group,register,value,unit\n"

  @staticmethod
  def get_csv_lines(
    holder: DeyeRegistersHolder,
    loggers: DeyeLoggers,
  ) -> List[str]:
    result: List[str] = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for inverter, registers in holder.all_registers.items():
      for register in registers.all_registers:
        is_accumulated = registers.prefix == loggers.accumulated_registers_prefix

        if is_accumulated and register.can_accumulate == False:
          continue

        is_slave = inverter != loggers.master.name
        is_only_master = register.avg_type == DeyeRegisterAverageType.only_master

        if is_slave and (register.can_write or is_only_master):
          continue

        result.append(f"{timestamp},{inverter},{register.group.title},"
                      f"{register.description},{register.pretty_value},{register.suffix}")

    return result
