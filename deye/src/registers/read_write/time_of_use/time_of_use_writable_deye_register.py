from typing import Any, List

from time_of_use_data import TimeOfUseData
from time_of_use_item import TimeOfUseItem
from time_of_use_time import TimeOfUseTime
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from time_of_use_week import TimeOfUseWeek

class TimeOfUseWritableDeyeRegister(BaseDeyeRegister):
  def __init__(
    self,
    charge_address: int,
    time_address: int,
    power_address: int,
    soc_address: int,
    weekly_address: int,
    min_soc: int,
    max_power: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(
      address = 0,
      quantity = 0,
      name = name,
      description = description,
      suffix = suffix,
      avg = avg,
    )
    self.charge_address = charge_address
    self.time_address = time_address
    self.power_address = power_address
    self.weekly_address = weekly_address
    self.soc_address = soc_address
    self.min_soc = min_soc
    self.max_power = max_power
    self.items_count = 6

  @property
  def addresses(self) -> List[int]:
    return list(range(self.charge_address, self.charge_address + self.items_count)) + \
      list(range(self.time_address, self.time_address + self.items_count)) + \
      list(range(self.power_address, self.power_address + self.items_count)) + \
      list(range(self.soc_address, self.soc_address + self.items_count)) + \
      [self.weekly_address]

  def enqueue(self, interactor: DeyeModbusInteractor) -> None:
    if interactor.is_master or self._avg != DeyeRegisterAverageType.only_master:
      interactor.enqueue_register(self.charge_address, self.items_count, self.caching_time)
      interactor.enqueue_register(self.time_address, self.items_count, self.caching_time)
      interactor.enqueue_register(self.power_address, self.items_count, self.caching_time)
      interactor.enqueue_register(self.soc_address, self.items_count, self.caching_time)
      interactor.enqueue_register(self.weekly_address, 1, self.caching_time)

  def read_internal(self, interactor: DeyeModbusInteractor) -> Any:
    charges = interactor.read_register(self.charge_address, self.items_count)
    times = interactor.read_register(self.time_address, self.items_count)
    powers = interactor.read_register(self.power_address, self.items_count)
    socs = interactor.read_register(self.soc_address, self.items_count)
    week = interactor.read_register(self.weekly_address, 1)[0]

    items: List[TimeOfUseItem] = []

    for index, _ in enumerate(times):
      # Ensure the number is 4 digits with leading zeros
      time_value = f"{times[index]:04d}"

      # Extract hours and minutes
      time = TimeOfUseTime(
        hour = int(time_value[:2]),
        minute = int(time_value[-2:]),
      )

      charge = charges[index]

      items.append(
        TimeOfUseItem(
          time = time,
          power = powers[index],
          soc = socs[index],
          grid_charge = bool(charge & 1),
          gen_charge = bool((charge >> 1) & 1),
        ))

      weekly = TimeOfUseWeek(
        monday = bool(week & (1 << 1)),
        tuesday = bool(week & (1 << 2)),
        wednesday = bool(week & (1 << 3)),
        thursday = bool(week & (1 << 4)),
        friday = bool(week & (1 << 5)),
        saturday = bool(week & (1 << 6)),
        sunday = bool(week & (1 << 7)),
      )

    return TimeOfUseData(
      enabled = bool(week & (1 << 0)),
      items = items,
      weekly = weekly,
    )

  def write(self, interactor: DeyeModbusInteractor, value) -> Any:
    if not isinstance(value, TimeOfUseData):
      self.error(f'write(): value should be of type {TimeOfUseData.__name__}')

    try:
      value.validate(min_soc = self.min_soc, max_power = self.max_power)
    except Exception as e:
      self.error(f'write(): {str(e)}')

    # for chagres some strange bit2 is set:
    # bit0 - grid charge
    # bit1 - gen charge
    # bit2 - is set to 1 - unknown bit. need to set to 1?
    # as example: if we set grid charge = true, gen charge = true
    # we will receive 7, but not 3 as int value, because of
    # bit2 is set to 1
    # for now write of charge settings not supported

    times = [item.time.hour * 100 + item.time.minute for item in value.items]
    powers = [item.power for item in value.items]
    socs = [item.soc for item in value.items]

    if interactor.write_register(self.time_address, times) != len(times):
      self.error(f'write(): something went wrong while writing {self.description}')

    if interactor.write_register(self.power_address, powers) != len(powers):
      self.error(f'write(): something went wrong while writing {self.description}')

    if interactor.write_register(self.soc_address, socs) != len(socs):
      self.error(f'write(): something went wrong while writing {self.description}')

    self._value = value
    return value
