from typing import List

from deye_logger import DeyeLogger
from pysolarmanv5 import PySolarmanV5

class DeyeModbusSolarman:
  def __init__(self, logger: DeyeLogger, **kwargs):
    self.logger = logger
    self.kwargs = kwargs
    self.modbus: PySolarmanV5 = None
    self.verbose = kwargs.get('verbose', False)

  def read_holding_registers(self, address: int, quantity: int) -> List[int]:
    if self.verbose:
      print(f"{self.logger.name}: reading data from inverter for address = {address}, quantity = {quantity}")

    if self.modbus is None:
      self.modbus = PySolarmanV5(
        self.logger.address,
        self.logger.serial,
        port = self.logger.port,
        **self.kwargs,
      )

    return self.modbus.read_holding_registers(address, quantity)

  def write_multiple_holding_registers(self, address: int, values: List[int]) -> int:
    if self.modbus is None:
      self.modbus = PySolarmanV5(
        self.logger.address,
        self.logger.serial,
        port = self.logger.port,
        **self.kwargs,
      )

    return self.modbus.write_multiple_holding_registers(address, values)

  def disconnect(self) -> None:
    if self.modbus is not None:
      try:
        self.modbus.disconnect()
      except Exception as e:
        if self.verbose:
          print(f'{self.logger.name}: error while disconnecting from inverter')
        raise
      finally:
        self.modbus = None
