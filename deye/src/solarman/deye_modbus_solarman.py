from deye_utils import *
from deye_logger import DeyeLogger
from deye_file_lock import lock_path
from deye_cache_manager import DeyeCacheManager
from pysolarmanv5 import PySolarmanV5

class DeyeModbusSolarman:
  def __init__(self, logger: DeyeLogger, **kwargs):
    self.logger = logger
    self.kwargs = kwargs
    self.modbus = None

    self.verbose = kwargs.get('verbose', False)
    caching_time = kwargs.get('caching_time', 3)

    # Ensure cache directory exists
    ensure_dir_exists(lock_path, mode = 0o777)

    # Initialize cache manager
    self.cache_manager = DeyeCacheManager(self.logger.name, lock_path, caching_time, verbose = self.verbose)

  def read_holding_registers(self, register_addr, quantity):
    data = self.cache_manager.load_from_cache(register_addr, quantity)
    if data is None:
      if self.verbose:
        print(f"{self.logger.name}: reading data from inverter for address = {register_addr}, quantity = {quantity}")
      if self.modbus is None:
        self.modbus = PySolarmanV5(self.logger.ip, self.logger.serial, port = self.logger.port, **self.kwargs)

      data = self.modbus.read_holding_registers(register_addr, quantity)
      self.cache_manager.save_to_cache(register_addr, quantity, data)

    return data

  def write_multiple_holding_registers(self, register_addr, values):
    if self.modbus is None:
      self.modbus = PySolarmanV5(self.logger.ip, self.logger.serial, port = self.logger.port, **self.kwargs)

    data = self.modbus.write_multiple_holding_registers(register_addr, values)
    self.cache_manager.remove_overlapping(register_addr, values)
    self.cache_manager.save_to_cache(register_addr, len(values), values)

    return data

  def disconnect(self):
    if self.modbus is not None:
      try:
        self.modbus.disconnect()
      except Exception as e:
        if self.verbose:
          print(f'{self.logger.name}: error while disconnecting from inverter')
        raise
      finally:
        self.modbus = None
