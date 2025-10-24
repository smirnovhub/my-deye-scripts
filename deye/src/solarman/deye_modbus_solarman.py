from typing import List
from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_file_lock import DeyeFileLock
from deye_cache_manager import DeyeCacheManager
from pysolarmanv5 import PySolarmanV5

class DeyeModbusSolarman:
  def __init__(self, logger: DeyeLogger, **kwargs):
    self.logger = logger
    self.kwargs = kwargs
    self.modbus: PySolarmanV5 = None

    self.verbose = kwargs.get('verbose', False)
    caching_time = kwargs.get('caching_time', 3)

    # Ensure cache directory exists
    DeyeUtils.ensure_dir_exists(DeyeFileLock.lock_path, mode = 0o777)

    # Initialize cache manager
    self.cache_manager = DeyeCacheManager(
      self.logger.name,
      DeyeFileLock.lock_path,
      caching_time,
      verbose = self.verbose,
    )

  def read_holding_registers(self, register_addr: int, quantity: int) -> List[int]:
    data = self.cache_manager.load_from_cache(register_addr, quantity)
    if data is None:
      if self.verbose:
        print(f"{self.logger.name}: reading data from inverter for address = {register_addr}, quantity = {quantity}")
      if self.modbus is None:
        self.modbus = PySolarmanV5(self.logger.address, self.logger.serial, port = self.logger.port, **self.kwargs)

      data = self.modbus.read_holding_registers(register_addr, quantity)
      self.cache_manager.save_to_cache(register_addr, quantity, data)

    return data

  def write_multiple_holding_registers(self, register_addr: int, values: List[int]) -> int:
    if self.modbus is None:
      self.modbus = PySolarmanV5(self.logger.address, self.logger.serial, port = self.logger.port, **self.kwargs)

    count = self.modbus.write_multiple_holding_registers(register_addr, values)
    self.cache_manager.remove_overlapping(register_addr, values)
    self.cache_manager.save_to_cache(register_addr, len(values), values)

    return count

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
