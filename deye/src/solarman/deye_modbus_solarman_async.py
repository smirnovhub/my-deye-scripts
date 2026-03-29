import logging

from typing import List

from deye_logger import DeyeLogger
from pysolarmanv5 import PySolarmanV5Async

class DeyeModbusSolarmanAsync:
  def __init__(self, logger: DeyeLogger, **kwargs):
    self._logger = logger
    self._kwargs = kwargs
    self._log = logging.getLogger()
    self._modbus: PySolarmanV5Async = None
    self._verbose = kwargs.get('verbose', False)

  async def read_holding_registers(self, address: int, quantity: int) -> List[int]:
    if self._verbose:
      self._log.info(f"{self._logger.name}: reading data from inverter for address = {address}, quantity = {quantity}")

    if self._modbus is None:
      self._modbus = PySolarmanV5Async(
        self._logger.address,
        self._logger.serial,
        port = self._logger.port,
        **self._kwargs,
      )

    return await self._modbus.read_holding_registers(address, quantity)

  async def write_multiple_holding_registers(self, address: int, values: List[int]) -> int:
    if self._modbus is None:
      self._modbus = PySolarmanV5Async(
        self._logger.address,
        self._logger.serial,
        port = self._logger.port,
        **self._kwargs,
      )

    return await self._modbus.write_multiple_holding_registers(address, values)

  async def disconnect(self) -> None:
    if self._modbus is not None:
      try:
        await self._modbus.disconnect()
      except Exception as e:
        if self._verbose:
          self._log.error(f'{self._logger.name}: error while disconnecting from inverter')
        raise
      finally:
        self._modbus = None
