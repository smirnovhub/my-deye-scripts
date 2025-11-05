from typing import Dict, List
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_modbus_solarman import DeyeModbusSolarman

class DeyeModbusInteractor:
  def __init__(self, logger: DeyeLogger, **kwargs):
    self.logger = logger
    self.loggers = DeyeLoggers()
    self.solarman = DeyeModbusSolarman(logger, **kwargs)
    self.registers_queue: Dict[int, int] = dict()
    self.verbose = kwargs.get('verbose', False)
    self.max_register_count = 120

  @property
  def name(self) -> str:
    return self.logger.name

  @property
  def is_master(self) -> bool:
    return self.logger.name == self.loggers.master.name

  def clear_registers_queue(self) -> None:
    self.registers_queue.clear()

  def enqueue_register(self, register_addr: int, quantity: int) -> None:
    for i in range(quantity):
      self.registers_queue[register_addr + i] = 0

  def process_enqueued_registers(self) -> None:
    if len(self.registers_queue) == 0:
      return

    sorted_queue = dict(sorted(self.registers_queue.items()))
    end_address = max(sorted_queue.keys())

    groups = []
    registers = []

    for item in sorted_queue:
      registers.append(item)
      count = max(registers) - min(registers)

      if count >= self.max_register_count:
        registers.pop()
        groups.append(list(registers))
        registers.clear()
        registers.append(item)

      if item == end_address:
        groups.append(list(registers))

    if self.verbose:
      test = str(groups).replace("], ", "],\n  ").replace("[[", "[\n  [").replace("]]", "]\n]")
      print(f'register groups to read from {self.logger.name}:')
      print(test)

    for group in groups:
      start = min(group)
      count = max(group) - start + 1

      data = self.solarman.read_holding_registers(register_addr = start, quantity = count)

      for idx, value in enumerate(data):
        if (idx + start) in group:
          self.registers_queue[idx + start] = value

  def read_register(self, register_addr: int, quantity: int) -> List[int]:
    result = []

    for i in range(quantity):
      key = register_addr + i
      result.append(self.registers_queue[key] if key in self.registers_queue else 0)

    return result

  def write_register(self, register_addr: int, values: List[int]) -> int:
    return self.solarman.write_multiple_holding_registers(register_addr, values)

  def disconnect(self) -> None:
    self.solarman.disconnect()
