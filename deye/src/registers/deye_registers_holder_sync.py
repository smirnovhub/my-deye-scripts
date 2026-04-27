from typing import Callable, Dict, List, Optional, cast
from concurrent.futures import Future, ThreadPoolExecutor, wait, ALL_COMPLETED

from deye_utils import DeyeUtils
from deye_logger import DeyeLogger
from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_exceptions import DeyeValueException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_registers_holder import DeyeRegistersHolder
from deye_register_cache_hit_rate import DeyeRegisterCacheHitRate
from deye_modbus_interactor_sync import DeyeModbusInteractorSync

class DeyeRegistersHolderSync(DeyeRegistersHolder):
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

    self._interactors: List[DeyeModbusInteractorSync] = []
    self._master_interactor: Optional[DeyeModbusInteractorSync] = None
    self._cache_available = False

    for logger in self._loggers:
      interactor = DeyeModbusInteractorSync(logger = logger, **kwargs)
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

  def get_cache_hit_rates(self) -> Dict[str, DeyeRegisterCacheHitRate]:
    return {interactor.name: interactor.get_cache_hit_rate() for interactor in self._interactors}

  def read_registers(self) -> None:
    if not self._interactors:
      raise DeyeValueException(f'{type(self).__name__}: interactors list is empty')

    if not self._cache_available:
      self._cache_available = self._interactors[0].is_cache_available()

    # Get the first available DeyeRegisters object from the values
    registers = next(iter(self.all_registers.values())).all_registers

    # We use a ThreadPoolExecutor for better management of concurrent tasks
    with ThreadPoolExecutor(max_workers = len(self._interactors)) as executor:
      future_to_interactor: Dict[Future[None], DeyeModbusInteractorSync] = {}

      # Enqueue and create tasks for all interactors
      for interactor in self._interactors:
        try:
          for register in registers:
            register.enqueue(interactor)

          # Submit the task to the pool
          future: Future[None] = executor.submit(interactor.process_enqueued_registers)
          future_to_interactor[future] = interactor
        except Exception as e:
          raise DeyeUtils.get_reraised_exception(
            e,
            f'{type(self).__name__}: error while enqueue {interactor.name}',
          ) from e

      try:
        # We wait for all tasks, but with a timeout to prevent total hang
        done, not_done = wait(
          future_to_interactor.keys(),
          timeout = self._socket_timeout + 3,
          return_when = ALL_COMPLETED,
        )

        # To replicate your exception handling, we check completed futures.
        # Calling future.result() will re-raise the exception from the thread.
        for future in done:
          future.result()

        # If there are tasks that didn't finish in time, we can treat it as an error
        if not_done:
          timed_out = [future_to_interactor[f].name for f in not_done]
          raise TimeoutError(f"Some interactors timed out: {', '.join(timed_out)}")

      except Exception as e:
        # This matches your original error handling style
        raise DeyeUtils.get_reraised_exception(e, f'{type(self).__name__}: error while reading registers') from e

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

  def write_register(self, register: DeyeRegister, value) -> None:
    if self._master_interactor == None:
      raise DeyeValueException(f'{type(self).__name__}: need to set master inverter before write')

    if not self._cache_available:
      self._cache_available = self._master_interactor.is_cache_available()

    try:
      register.write(self._master_interactor, value)
      self._master_interactor.write_registers_to_inverter()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(e, f'{type(self).__name__}: error while writing register') from e

  def reset_cache(self) -> None:
    for interactor in self._interactors:
      interactor.reset_cache()

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
