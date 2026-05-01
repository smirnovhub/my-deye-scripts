from typing import Any

from base_deye_register import BaseDeyeRegister
from deye_register_group import DeyeRegisterGroup
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class TestDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    address: int,
    quantity: int,
    description: str,
    suffix: str,
    group: DeyeRegisterGroup,
  ):
    super().__init__(
      address = address,
      quantity = quantity,
      description = description,
      suffix = suffix,
      group = group,
    )
    self._value = 0

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    if not interactor.is_master and self._avg == DeyeRegisterAverageType.only_master:
      return

    max_count = 10

    # Split into multiple chunks to enqueue each separately
    for i in range(0, self.quantity, max_count):
      chunk_addr = self.address + i
      chunk_quantity = min(max_count, self.quantity - i)

      interactor.enqueue_register(chunk_addr, chunk_quantity, self.caching_time)

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    values = interactor.read_register(self.address, self.quantity)
    for index, value in enumerate(values):
      print(f"{self.address + index} = {value}")

    return 0
