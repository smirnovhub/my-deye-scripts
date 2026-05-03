import random
import threading

from typing import Dict, List, Set

from solarman_base_server import SolarmanBaseServer

from umodbus.functions import (
  ReadHoldingRegisters,
  ReadInputRegisters,
  WriteMultipleRegisters,
  ReadCoils,
)

class SolarmanTestServer(SolarmanBaseServer):
  def __init__(
    self,
    name: str,
    address: str,
    serial: int,
    port: int = 8899,
  ):
    super().__init__(
      name = name,
      address = address,
      serial = serial,
      port = port,
    )
    self._registers: Dict[int, int] = {}
    self._readed_registers: Set[int] = set()
    self._written_registers: Set[int] = set()
    self._random_values_on_read: bool = False
    self._sequential_values_on_read: bool = False
    self._lock = threading.Lock()

  def set_random_mode(self, rnd_mode: bool) -> None:
    """
    Enables or disables random value generation when reading registers.

    When this mode is enabled (True), all register read operations
    will return random values instead of actual data. This is useful for testing
    and simulation purposes.

    :param rnd_mode: True to enable random values on read, False to disable.
    """
    self._random_values_on_read = rnd_mode

  def set_sequential_mode(self, seq_mode: bool) -> None:
    self._sequential_values_on_read = seq_mode

  def set_register_value(self, address: int, value: int) -> None:
    """
    Set the value of a single register (for testing purposes).

    This method is intended for simulating device registers in a test
    environment. It updates the internal register dictionary and logs the change.

    Parameters
    ----------
    address : int
        The address of the register to set.
    value : int
        The value to store in the register.
    """
    with self._lock:
      self._log.info(f"{self._name}: setting register value {{{address}: {value}}}")
      self._registers[address] = value

  def set_register_values(self, addresses: List[int], values: List[int]) -> None:
    """
    Set multiple register values starting from a given address (for testing purposes).

    This method is intended for simulating device registers in a test environment.
    It updates the internal register dictionary and logs all changes.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to set.
    values : List[int]
        The list of values to store in consecutive registers.
    """
    if len(addresses) != len(values):
      raise ValueError(f"{self._name}: addresses count ({len(addresses)}) should be "
                       f"the same as values count ({len(values)})")

    self._log.info(f"{self._name}: setting register addresses {addresses} to values {values}")

    with self._lock:
      for i, address in enumerate(addresses):
        self._registers[address] = values[i]

  def clear_registers(self) -> None:
    """
    Clear all register values (for testing purposes).

    This method resets the internal register dictionary, effectively
    simulating a device with no stored values.
    """
    with self._lock:
      self._registers.clear()

  def clear_registers_status(self) -> None:
    """
    Clear the read and written registers tracking (for testing purposes).

    This method resets the sets that track which registers have been read
    or written, simulating a fresh device state for testing.
    """
    with self._lock:
      self._readed_registers.clear()
      self._written_registers.clear()

  def is_registers_readed(self, starting_address: int, quantity: int) -> bool:
    """
    Check if a range of registers has been read (for testing purposes).

    This method returns True if all registers in the specified range
    have been marked as read in the internal tracking set.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to check.
    quantity : int
        The number of consecutive registers to check.

    Returns
    -------
    bool
        True if all specified registers have been read, False otherwise.
    """
    with self._lock:
      for address in range(starting_address, starting_address + quantity):
        if address not in self._readed_registers:
          return False
    return True

  def is_registers_written(self, starting_address: int, quantity: int) -> bool:
    """
    Check if a range of registers has been written (for testing purposes).

    This method returns True if all registers in the specified range
    have been marked as written in the internal tracking set.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to check.
    quantity : int
        The number of consecutive registers to check.

    Returns
    -------
    bool
        True if all specified registers have been written, False otherwise.
    """
    with self._lock:
      for address in range(starting_address, starting_address + quantity):
        if address not in self._written_registers:
          return False
    return True

  def is_something_written(self) -> bool:
    with self._lock:
      return bool(self._written_registers)

  def get_new_registers_values(self, starting_address: int, values: List[int]) -> Dict[int, int]:
    """
    Map a list of values to consecutive register addresses (for testing purposes).

    This method creates a dictionary that assigns each value to a register
    address starting from `starting_address`. Useful for simulating writes
    to multiple registers in a test environment.

    Parameters
    ----------
    starting_address : int
        The starting address for the registers.
    values : List[int]
        The list of values to assign to consecutive registers.

    Returns
    -------
    Dict[int, int]
        A dictionary mapping register addresses to their corresponding values.
    """
    registers: Dict[int, int] = {}
    start = starting_address
    for offset, value in enumerate(values):
      registers[start + offset] = value
    return registers

  def get_existing_registers_values(self, starting_address: int, quantity: int) -> List[int]:
    """
    Retrieve values of consecutive registers (for testing purposes).

    This method returns a list of register values starting from `starting_address`.
    If a register has not been set, its value defaults to 0. Useful for simulating
    reads from a device in a test environment.

    Parameters
    ----------
    starting_address : int
        The starting address of the registers to read.
    quantity : int
        The number of consecutive registers to retrieve.

    Returns
    -------
    List[int]
        A list of register values corresponding to the requested addresses.
    """
    with self._lock:
      return [self._registers.get(i, 0) for i in range(
        starting_address,
        starting_address + quantity,
      )]

  def on_read_coils(self, func: ReadCoils) -> bytes:
    if func.quantity is None:
      raise ValueError("ReadCoils request missing quantity")
    return func.create_response_pdu([random.randint(0, 255) for x in range(func.quantity)])

  def on_read_holding_registers(self, func: ReadHoldingRegisters) -> bytes:
    if func.quantity is None or func.starting_address is None:
      raise ValueError("ReadHoldingRegisters request missing starting_address or quantity")

    if self._random_values_on_read:
      read_values = [random.randint(0, 2**16 - 1) for x in range(func.quantity)]
    elif self._sequential_values_on_read:
      read_values = [int(func.starting_address) + x for x in range(func.quantity)]
    else:
      read_values = self.get_existing_registers_values(func.starting_address, func.quantity)

    new_values = self.get_new_registers_values(func.starting_address, read_values)

    with self._lock:
      for address in new_values.keys():
        self._readed_registers.add(address)

    self._log.info(f'{self._name}: read registers {new_values}')
    return func.create_response_pdu(read_values)

  def on_read_input_registers(self, func: ReadInputRegisters) -> bytes:
    if func.quantity is None:
      raise ValueError("ReadInputRegisters request missing quantity")
    return func.create_response_pdu([random.randint(0, 2**16 - 1) for x in range(func.quantity)])

  def on_write_multiple_registers(self, func: WriteMultipleRegisters) -> bytes:
    if func.starting_address is None or func.values is None:
      raise ValueError("ReadHoldingRegisters request missing starting_address or values")

    write_values = self.get_new_registers_values(func.starting_address, func.values)

    with self._lock:
      self._registers.update(write_values)

    with self._lock:
      for address in write_values.keys():
        self._written_registers.add(address)

    self._log.info(f'{self._name}: write registers {write_values}')
    return func.create_response_pdu()
