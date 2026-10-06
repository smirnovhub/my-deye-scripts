import zlib

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List
from deye_registers import DeyeRegisters
from deye_utils import DeyeUtils

class BaseDeyeVirtualRegister(ABC):
  def __init__(
    self,
    start_address: int,
    quantity: int,
  ):
    self._start_address = start_address
    self._quantity = quantity

  def has_address(self, address: int) -> bool:
    # Check if address falls within the provider range using simple math
    return self._start_address <= address < (self._start_address + self._quantity)

  @property
  def start_address(self) -> int:
    return self._start_address

  @property
  @abstractmethod
  def caching_time(self) -> timedelta:
    pass

  @abstractmethod
  def generate_values(self) -> List[int]:
    pass

class DeyeSystemTimeVirtualRegister(BaseDeyeVirtualRegister):
  def __init__(
    self,
    start_address: int,
    quantity: int,
  ):
    super().__init__(start_address, quantity)

  @property
  def caching_time(self) -> timedelta:
    return timedelta(seconds = 30)

  def generate_values(self) -> List[int]:
    now = datetime.now()
    return DeyeUtils.to_inv_time([
      now.year - 2000,
      now.month,
      now.day,
      now.hour,
      now.minute,
      now.second,
    ])

class DeyeSerialNumberVirtualRegister(BaseDeyeVirtualRegister):
  def __init__(
    self,
    start_address: int,
    quantity: int,
    serial_number: str,
  ):
    super().__init__(start_address, quantity)

    sn = serial_number.ljust(quantity * 2, ' ')[:quantity * 2]
    self._values: List[int] = []
    for i in range(quantity):
      high_byte = ord(sn[i * 2])
      low_byte = ord(sn[i * 2 + 1])
      self._values.append((high_byte << 8) | low_byte)

  @property
  def caching_time(self) -> timedelta:
    return timedelta(hours = 24)

  def generate_values(self) -> List[int]:
    return self._values

class DeyeVirtualRegisterProvider:
  def __init__(
    self,
    serial: int,
  ) -> None:
    registers = DeyeRegisters()

    self._virtual_registers: List[BaseDeyeVirtualRegister] = [
      DeyeSystemTimeVirtualRegister(
        start_address = registers.inverter_system_time_register.address,
        quantity = registers.inverter_system_time_register.quantity,
      ),
      DeyeSerialNumberVirtualRegister(
        start_address = registers.inverter_serial_number_register.address,
        quantity = registers.inverter_serial_number_register.quantity,
        serial_number = self._hash_crc32_str(serial),
      ),
    ]

  def _hash_crc32_str(self, number: int) -> str:
    num_str = str(number)
    length = len(num_str)

    # Calculate CRC32 checksum
    raw_crc = zlib.crc32(num_str.encode())

    # Format with exact digit count using leading zeros
    return f"{raw_crc % (10 ** length):0{length}d}"

  @property
  def virtual_registers(self) -> List[BaseDeyeVirtualRegister]:
    return self._virtual_registers

  def is_virtual_register(self, address: int) -> bool:
    return any(reg.has_address(address) for reg in self._virtual_registers)
