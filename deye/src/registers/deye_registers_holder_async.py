import asyncio

from typing import Callable, Dict, List, Optional, cast

from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_exceptions import DeyeValueException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_registers_holder import DeyeRegistersHolder
from deye_register_cache_hit_rate import DeyeRegisterCacheHitRate
from deye_modbus_interactor_async import DeyeModbusInteractorAsync

class DeyeRegistersHolderAsync(DeyeRegistersHolder):
  def __init__(
    self,
    loggers: List[DeyeLogger],
    register_creator: Optional[Callable[[str], DeyeRegisters]] = None,
    **kwargs,
  ):
    super().__init__(
      loggers = loggers,
      **kwargs,
    )

    self._interactors: List[DeyeModbusInteractorAsync] = []
    self._master_interactor: Optional[DeyeModbusInteractorAsync] = None
    self._cache_available = False

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

  @property
  def cache_hit_rates(self) -> Dict[str, DeyeRegisterCacheHitRate]:
    return {interactor.name: interactor.cache_hit_rate for interactor in self._interactors}

  async def get_cache_hit_rates(self) -> Dict[str, DeyeRegisterCacheHitRate]:
    # Create a list of coroutines
    tasks = [interactor.get_cache_hit_rate() for interactor in self._interactors]

    # Run them concurrently and wait for all results
    rates = await asyncio.gather(*tasks)

    # Map interactor names to their respective results
    return {interactor.name: rate for interactor, rate in zip(self._interactors, rates)}

  async def read_registers(self) -> None:
    if not self._interactors:
      raise DeyeValueException(f'{type(self).__name__}: interactors list is empty')

    if not self._cache_available:
      self._cache_available = await self._interactors[0].is_cache_available()

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
          timeout = self._socket_timeout + 3,
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

  async def write_register(self, register: DeyeRegister, value) -> None:
    if self._master_interactor == None:
      raise DeyeValueException(f'{type(self).__name__}: need to set master inverter before write')

    if not self._cache_available:
      self._cache_available = await self._master_interactor.is_cache_available()

    try:
      register.write(self._master_interactor, value)
      await self._master_interactor.write_registers_to_inverter()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{type(self).__name__}: error while writing register') from e

  async def reset_cache(self) -> None:
    tasks = [interactor.reset_cache() for interactor in self._interactors]
    await asyncio.gather(*tasks)

  def disconnect(self) -> None:
    self._cache_available = False

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
