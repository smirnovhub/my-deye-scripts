import os
import time
import logging

from typing import Callable, Dict, List, Optional

from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from raising_thread import RaisingThread
from deye_file_locker import DeyeFileLocker
from deye_exceptions import DeyeValueException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_registers_factory import DeyeRegistersFactory
from lock_exceptions import DeyeLockAlreadyAcquiredException
from deye_exceptions import DeyeNoSocketAvailableException
from deye_exceptions import DeyeQueueIsEmptyException

from deye_utils import (
  get_reraised_exception,
  get_test_retry_count,
  is_tests_on,
)

from deye_file_lock import (
  lock_path,
  inverter_lock_file_name,
)

class DeyeRegistersHolder:
  def __init__(
    self,
    loggers: List[DeyeLogger],
    register_creator: Optional[Callable[[str], DeyeRegisters]] = None,
    **kwargs,
  ):
    self._registers: Dict[str, DeyeRegisters] = {}
    self._interactors: List[DeyeModbusInteractor] = []
    self._master_interactor: Optional[DeyeModbusInteractor] = None
    self._loggers = loggers
    self.log = logging.getLogger()
    self._all_loggers = DeyeLoggers()

    # Initialize locker
    verbose = kwargs.get('verbose', False)
    name = kwargs.get('name', os.path.basename(__file__))
    lockfile = os.path.join(lock_path, inverter_lock_file_name)
    self.locker = DeyeFileLocker(name, lockfile, verbose = verbose)

    for logger in self._loggers:
      interactor = DeyeModbusInteractor(logger = logger, **kwargs)
      self._interactors.append(interactor)

      if register_creator is not None:
        self._registers[logger.name] = register_creator(logger.name)
      else:
        self._registers[logger.name] = DeyeRegistersFactory.create_registers(prefix = logger.name)

      if interactor.is_master:
        self._master_interactor = interactor

    if register_creator is not None:
      accumulated_registers = register_creator(self._all_loggers.accumulated_registers_prefix)
    else:
      accumulated_registers = DeyeRegistersFactory.create_registers(
        prefix = self._all_loggers.accumulated_registers_prefix)

    self._registers[self._all_loggers.accumulated_registers_prefix] = accumulated_registers

  @property
  def all_registers(self) -> Dict[str, DeyeRegisters]:
    return self._registers

  @property
  def master_registers(self) -> DeyeRegisters:
    return self._registers[self._all_loggers.master.name]

  @property
  def accumulated_registers(self) -> DeyeRegisters:
    return self._registers[self._all_loggers.accumulated_registers_prefix]

  def read_registers(self):
    def log_retry(attempt, retry_count, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                    f'{str(exception)}, retrying... (attempt {attempt}/{retry_count})')

    if is_tests_on():
      retry_count = get_test_retry_count()
      self._read_registers_with_retry_internal(retry_count = retry_count, on_retry = log_retry)
    else:
      self._read_registers_internal()

  def _read_registers_internal(self):
    try:
      self.locker.acquire()
    except DeyeLockAlreadyAcquiredException:
      pass

    tasks: List[RaisingThread] = []

    for interactor in self._interactors:
      try:
        for register in list(self.all_registers.values())[0].all_registers:
          register.enqueue(interactor)
        tasks.append(
          RaisingThread(target = interactor.process_enqueued_registers, name = interactor.name.title() + "Thread"))
      except Exception as e:
        raise get_reraised_exception(e,
                                     f'{type(self).__name__}: error while enqueue {interactor.name} registers') from e

    try:
      for task in tasks:
        task.start()

      for task in tasks:
        task.join()
    except Exception as e:
      raise get_reraised_exception(e, f'{type(self).__name__}: error while reading registers') from e

    for interactor in self._interactors:
      try:
        for register in self._registers[interactor.name].all_registers:
          register.read([interactor])
      except Exception as e:
        raise get_reraised_exception(e,
                                     f'{type(self).__name__}: error while reading {interactor.name} registers') from e

    for register in self.accumulated_registers.all_registers:
      try:
        register.read(self._interactors)
      except Exception as e:
        raise get_reraised_exception(e, f'{type(self).__name__}: error while reading register {register.name}') from e

    for register in self.accumulated_registers.forecast_registers:
      try:
        register.read(self._interactors)
      except Exception as e:
        raise get_reraised_exception(e, f'{type(self).__name__}: error while reading register {register.name}') from e

  def _read_registers_with_retry_internal(
    self,
    retry_count = 3,
    retry_delay = 3,
    on_retry: Optional[Callable[[int, int, Exception], None]] = None,
  ):
    last_exception: Optional[Exception] = None
    for i in range(retry_count):
      try:
        self._read_registers_internal()
      except (DeyeNoSocketAvailableException, DeyeQueueIsEmptyException) as e:
        last_exception = e
        if on_retry:
          on_retry(i + 1, retry_count, e)
        time.sleep(retry_delay)
        continue
      break
    else:
      if last_exception is not None:
        raise last_exception

  def write_register(self, register: DeyeRegister, value):
    def log_retry(attempt, retry_count, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while writing registers: '
                    f'{str(exception)}, retrying... (attempt {attempt}/{retry_count})')

    if is_tests_on():
      retry_count = get_test_retry_count()
      return self._write_register_with_retry_internal(
        register,
        value,
        retry_count = retry_count,
        on_retry = log_retry,
      )
    else:
      return self._write_register_internal(register, value)

  def _write_register_internal(self, register: DeyeRegister, value):
    try:
      self.locker.acquire()
    except DeyeLockAlreadyAcquiredException:
      pass

    if self._master_interactor == None:
      raise DeyeValueException(f'{type(self).__name__}: need to set master inverter before write')

    try:
      return register.write(self._master_interactor, value)
    except Exception as e:
      raise get_reraised_exception(e, f'{type(self).__name__}: error while writing register') from e

  def _write_register_with_retry_internal(
    self,
    register: DeyeRegister,
    value,
    retry_count = 3,
    retry_delay = 3,
    on_retry: Optional[Callable[[int, int, Exception], None]] = None,
  ):
    last_exception: Optional[Exception] = None
    for i in range(retry_count):
      try:
        return self._write_register_internal(register, value)
      except (DeyeNoSocketAvailableException, DeyeQueueIsEmptyException) as e:
        last_exception = e
        if on_retry:
          on_retry(i + 1, retry_count, e)
        time.sleep(retry_delay)
        continue
    else:
      if last_exception is not None:
        raise last_exception

  def disconnect(self):
    last_exception = None
    try:
      for interactor in self._interactors:
        try:
          interactor.disconnect()
        except Exception as e:
          try:
            raise get_reraised_exception(
              e, f'{type(self).__name__}: error while disconnecting from inverter {interactor.name}') from e
          except Exception as handled:
            # remember last exception
            last_exception = handled
    finally:
      self.locker.release()

    if last_exception:
      raise last_exception
