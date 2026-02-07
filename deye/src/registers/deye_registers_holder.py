import os
import time
import logging

from typing import Any, Callable, Dict, List, Optional

from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from raising_thread import RaisingThread
from deye_file_lock import DeyeFileLock
from deye_base_locker import DeyeBaseLocker
from deye_empty_locker import DeyeEmptyLocker
from deye_exceptions import DeyeValueException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_exceptions import DeyeNoSocketAvailableException
from deye_exceptions import DeyeQueueIsEmptyException

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
    self.verbose = kwargs.get('verbose', False)
    self.name = kwargs.get('name', os.path.basename(__file__))
    suffix = '_test' if self._all_loggers.is_test_loggers else ''
    self.lockfile = os.path.join(DeyeFileLock.lock_path, DeyeFileLock.inverter_lock_file_name_template.format(suffix))

    for logger in self._loggers:
      interactor = DeyeModbusInteractor(logger = logger, **kwargs)
      self._interactors.append(interactor)

      if register_creator is not None:
        self._registers[logger.name] = register_creator(logger.name)
      else:
        self._registers[logger.name] = DeyeRegisters(prefix = logger.name)

      if interactor.is_master:
        self._master_interactor = interactor

    if register_creator is not None:
      accumulated_registers = register_creator(self._all_loggers.accumulated_registers_prefix)
    else:
      accumulated_registers = DeyeRegisters(prefix = self._all_loggers.accumulated_registers_prefix)

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

  def create_locker(self) -> DeyeBaseLocker:
    return DeyeEmptyLocker()

  def read_registers(self) -> None:
    def log_retry(attempt, total_attempts, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                    f'{str(exception)}, retrying... (attempt {attempt}/{total_attempts})')

    locker = self.create_locker()
    locker.acquire()

    try:
      if DeyeUtils.is_tests_on():
        retry_timeout = DeyeUtils.get_test_retry_timeout()
        self._read_registers_with_retry_internal(retry_timeout = retry_timeout, on_retry = log_retry)
      else:
        self._read_registers_internal()
    finally:
      locker.release()

  def _read_registers_internal(self) -> None:
    tasks: List[RaisingThread] = []

    for interactor in self._interactors:
      try:
        for register in list(self.all_registers.values())[0].all_registers:
          register.enqueue(interactor)
        tasks.append(
          RaisingThread(target = interactor.process_enqueued_registers, name = interactor.name.title() + "Thread"))
      except Exception as e:
        raise DeyeUtils.get_reraised_exception(
          e, f'{type(self).__name__}: error while enqueue {interactor.name} registers') from e

    try:
      for task in tasks:
        task.start()

      for task in tasks:
        task.join()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{type(self).__name__}: error while reading registers') from e

    for interactor in self._interactors:
      try:
        for register in self._registers[interactor.name].all_registers:
          register.read([interactor])
      except Exception as e:
        raise DeyeUtils.get_reraised_exception(
          e, f'{type(self).__name__}: error while reading {interactor.name} registers') from e

    for register in self.accumulated_registers.all_registers:
      try:
        register.read(self._interactors)
      except Exception as e:
        raise DeyeUtils.get_reraised_exception(
          e, f'{type(self).__name__}: error while reading register {register.name}') from e

  def _read_registers_with_retry_internal(
    self,
    retry_timeout,
    retry_delay = 1,
    on_retry: Optional[Callable[[int, int, Exception], None]] = None,
  ) -> None:
    last_exception: Optional[Exception] = None
    retry_attempt = 1
    total_retry_time = 0
    total_attempts = round(retry_timeout / retry_delay)

    while total_retry_time < retry_timeout:
      try:
        self._read_registers_internal()
        return
      except (DeyeNoSocketAvailableException, DeyeQueueIsEmptyException) as e:
        last_exception = e
        if on_retry:
          on_retry(retry_attempt, total_attempts, e)
        time.sleep(retry_delay)
        retry_attempt += 1
        total_retry_time += retry_delay
    else:
      if last_exception is not None:
        raise last_exception

  def write_register(self, register: DeyeRegister, value) -> Any:
    def log_retry(attempt, total_attempts, exception):
      self.log.info(f'{type(self).__name__}: an exception occurred while writing registers: '
                    f'{str(exception)}, retrying... (attempt {attempt}/{total_attempts})')

    locker = self.create_locker()
    locker.acquire()

    try:
      if DeyeUtils.is_tests_on():
        retry_timeout = DeyeUtils.get_test_retry_timeout()
        return self._write_register_with_retry_internal(
          register,
          value,
          retry_timeout = retry_timeout,
          on_retry = log_retry,
        )
      else:
        return self._write_register_internal(register, value)
    finally:
      locker.release()

  def _write_register_internal(self, register: DeyeRegister, value) -> Any:
    if self._master_interactor == None:
      raise DeyeValueException(f'{type(self).__name__}: need to set master inverter before write')

    try:
      return register.write(self._master_interactor, value)
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{type(self).__name__}: error while writing register') from e

  def _write_register_with_retry_internal(
    self,
    register: DeyeRegister,
    value,
    retry_timeout,
    retry_delay = 1,
    on_retry: Optional[Callable[[int, int, Exception], None]] = None,
  ) -> Any:
    last_exception: Optional[Exception] = None
    retry_attempt = 1
    total_retry_time = 0
    total_attempts = round(retry_timeout / retry_delay)

    while total_retry_time < retry_timeout:
      try:
        return self._write_register_internal(register, value)
      except (DeyeNoSocketAvailableException, DeyeQueueIsEmptyException) as e:
        last_exception = e
        if on_retry:
          on_retry(retry_attempt, total_attempts, e)
        time.sleep(retry_delay)
        retry_attempt += 1
        total_retry_time += retry_delay
    else:
      if last_exception is not None:
        raise last_exception

  # Deprecated
  def disconnect(self) -> None:
    pass
