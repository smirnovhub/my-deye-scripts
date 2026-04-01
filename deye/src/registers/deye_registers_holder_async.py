import os
import asyncio
import logging

from typing import Any, Callable, Dict, List, Optional, cast

from deye_utils import DeyeUtils
from env_utils import EnvUtils
from deye_logger import DeyeLogger
from deye_loggers import DeyeLoggers
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_file_lock import DeyeFileLock
from deye_exceptions import DeyeValueException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_modbus_interactor_async import DeyeModbusInteractorAsync
from deye_exceptions import DeyeNoSocketAvailableException
from deye_exceptions import DeyeQueueIsEmptyException

class DeyeRegistersHolderAsync:
  def __init__(
    self,
    loggers: List[DeyeLogger],
    register_creator: Optional[Callable[[str], DeyeRegisters]] = None,
    **kwargs,
  ):
    self._registers: Dict[str, DeyeRegisters] = {}
    self._interactors: List[DeyeModbusInteractorAsync] = []
    self._master_interactor: Optional[DeyeModbusInteractorAsync] = None
    self._loggers = loggers
    self._log = logging.getLogger()
    self._all_loggers = DeyeLoggers()

    # Initialize locker
    self.verbose = kwargs.get('verbose', False)
    self.name = kwargs.get('name', os.path.basename(__file__))
    suffix = '_test' if self._all_loggers.is_test_loggers else ''
    self.lockfile = os.path.join(DeyeFileLock.lock_path, DeyeFileLock.inverter_lock_file_name_template.format(suffix))

    for logger in self._loggers:
      interactor = DeyeModbusInteractorAsync(logger = logger, **kwargs)
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

  async def read_registers(self) -> None:
    def log_retry(attempt, total_attempts, exception):
      self._log.info(f'{type(self).__name__}: an exception occurred while reading registers: '
                     f'{str(exception)}, retrying... (attempt {attempt}/{total_attempts})')

    if EnvUtils.is_tests_on():
      retry_timeout = DeyeUtils.get_test_retry_timeout()
      await self._read_registers_with_retry_internal(retry_timeout = retry_timeout, on_retry = log_retry)
    else:
      await self._read_registers_internal()

  async def _read_registers_internal(self) -> None:
    # Get the first available DeyeRegisters object from the values
    registers = next(iter(self.all_registers.values())).all_registers

    tasks: List[asyncio.Task[None]] = []

    try:
      # Enqueue and create tasks for all interactors
      for interactor in self._interactors:
        try:
          for register in registers:
            register.enqueue(interactor)

          # Create an asyncio task for the interactor's processing logic
          # Using create_task starts execution immediately in the event loop
          coro = interactor.process_enqueued_registers()
          task = asyncio.create_task(coro, name = interactor.name)

          tasks.append(task)
        except Exception as e:
          raise DeyeUtils.get_reraised_exception(
            e, f'{type(self).__name__}: error while enqueueing {interactor.name}') from e

      if not tasks:
        return

      # Wait for all interactor tasks with a global timeout
      try:
        # asyncio.gather aggregates results and raises the first exception encountered
        await asyncio.wait_for(
          asyncio.gather(*tasks, return_exceptions = True),
          timeout = 10.0,
        )
      except asyncio.TimeoutError:
        # Identify which interactors failed to respond in time
        unfinished = [t.get_name() for t in tasks if not t.done()]

        # Cancel pending tasks to avoid background leaks
        for t in tasks:
          if not t.done():
            t.cancel()

        raise TimeoutError(f"Some interactors timed out: {', '.join(unfinished)}")
      except Exception as e:
        # Propagation of errors occurred during register processing
        raise DeyeUtils.get_reraised_exception(e, f'{type(self).__name__}: error while reading registers') from e

      # Check results after gather is finished
      for task in tasks:
        # Important: Check if task is NOT cancelled before calling .exception()
        if task.cancelled():
          continue

        exc = task.exception()

        # Reraise with context so we know which inverter failed
        if isinstance(exc, Exception):
          interactor_name = task.get_name()
          raise DeyeUtils.get_reraised_exception(
            exc,
            f"{type(self).__name__}: interactor '{interactor_name}' failed",
          ) from exc
    finally:
      # Mandatory cleanup to prevent background task leaks
      pending = [t for t in tasks if not t.done()]
      for t in pending:
        t.cancel()

      if pending:
        # Give the loop a chance to finish cancellation of tasks
        await asyncio.gather(*pending, return_exceptions = True)

    # Process individual interactor registers
    for interactor in self._interactors:
      try:
        # Assuming interactor.name matches the keys in self._registers
        for register in self._registers[interactor.name].all_registers:
          register.read([interactor])
      except Exception as e:
        raise DeyeUtils.get_reraised_exception(
          e, f'{type(self).__name__}: error while reading {interactor.name} registers') from e

    # Final step: read accumulated registers
    base_interactors = cast(List[DeyeModbusInteractor], self._interactors)
    for register in self.accumulated_registers.all_registers:
      try:
        register.read(base_interactors)
      except Exception as e:
        raise DeyeUtils.get_reraised_exception(
          e, f'{type(self).__name__}: error while reading register {register.name}') from e

  async def _read_registers_with_retry_internal(
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
        await self._read_registers_internal()
        return
      except (DeyeNoSocketAvailableException, DeyeQueueIsEmptyException) as e:
        last_exception = e
        if on_retry:
          on_retry(retry_attempt, total_attempts, e)
        await asyncio.sleep(retry_delay)
        retry_attempt += 1
        total_retry_time += retry_delay
    else:
      if last_exception is not None:
        raise last_exception

  async def write_register(self, register: DeyeRegister, value) -> Any:
    def log_retry(attempt, total_attempts, exception):
      self._log.info(f'{type(self).__name__}: an exception occurred while writing registers: '
                     f'{str(exception)}, retrying... (attempt {attempt}/{total_attempts})')

    if EnvUtils.is_tests_on():
      retry_timeout = DeyeUtils.get_test_retry_timeout()
      return await self._write_register_with_retry_internal(
        register,
        value,
        retry_timeout = retry_timeout,
        on_retry = log_retry,
      )
    else:
      return await self._write_register_internal(register, value)

  async def _write_register_internal(self, register: DeyeRegister, value) -> Any:
    if self._master_interactor == None:
      raise DeyeValueException(f'{type(self).__name__}: need to set master inverter before write')

    try:
      value = register.write(self._master_interactor, value)
      await self._master_interactor.write_registers_to_inverter()
      return value
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{type(self).__name__}: error while writing register') from e

  async def _write_register_with_retry_internal(
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
        return await self._write_register_internal(register, value)
      except (DeyeNoSocketAvailableException, DeyeQueueIsEmptyException) as e:
        last_exception = e
        if on_retry:
          on_retry(retry_attempt, total_attempts, e)
        await asyncio.sleep(retry_delay)
        retry_attempt += 1
        total_retry_time += retry_delay
    else:
      if last_exception is not None:
        raise last_exception

  async def reset_cache(self) -> None:
    tasks = [interactor.reset_cache() for interactor in self._interactors]
    await asyncio.gather(*tasks)

  def disconnect(self) -> None:
    last_exception = None

    for interactor in self._interactors:
      try:
        interactor.disconnect()
      except Exception as e:
        try:
          raise DeyeUtils.get_reraised_exception(
            e, f'{type(self).__name__}: error while disconnecting from inverter {interactor.name}') from e
        except Exception as handled:
          # remember last exception
          last_exception = handled

    if last_exception:
      raise last_exception
