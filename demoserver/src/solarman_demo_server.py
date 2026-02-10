from typing import Dict, List

from deye_registers import DeyeRegisters
from solarman_base_server import SolarmanBaseServer
from deye_test_helper import DeyeTestHelper

from umodbus.functions import (
  ReadHoldingRegisters,
  WriteMultipleRegisters,
)

class SolarmanDemoServer(SolarmanBaseServer):
  def __init__(
    self,
    name: str,
    address: str,
    serial: int,
    port: int = 8899,
  ):
    super().__init__(name, address, serial, port)
    self.registers_data: Dict[int, int] = {}
    self.registers = DeyeRegisters()

    for reg in self.registers.read_write_registers:
      random_value = DeyeTestHelper.get_random_by_register_type(reg)
      if random_value:
        for i, value in enumerate(random_value.values):
          self.registers_data[reg.address + i] = value

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
    return [self.registers_data.get(i, 0) for i in range(
      starting_address,
      starting_address + quantity,
    )]

  def on_read_holding_registers(self, func: ReadHoldingRegisters) -> bytes:
    if func.quantity is None or func.starting_address is None:
      raise ValueError("ReadHoldingRegisters request missing starting_address or quantity")

    reg = next((r for r in self.registers.all_registers if r.address == func.starting_address), None)
    if reg:
      random_value = DeyeTestHelper.get_random_by_register_type(reg)
      if random_value:
        for i, value in enumerate(random_value.values):
          self.registers_data[reg.address + i] = value

    read_values = self.get_existing_registers_values(func.starting_address, func.quantity)
    new_values = self.get_new_registers_values(func.starting_address, read_values)

    self.log.info(f'{self.name}: read registers {new_values}')
    return func.create_response_pdu(read_values)

  def on_write_multiple_registers(self, func: WriteMultipleRegisters) -> bytes:
    if func.starting_address is None or func.values is None:
      raise ValueError("ReadHoldingRegisters request missing starting_address or values")

    write_values = self.get_new_registers_values(func.starting_address, func.values)
    self.registers_data.update(write_values)

    self.log.info(f'{self.name}: write registers {write_values}')
    return func.create_response_pdu()
