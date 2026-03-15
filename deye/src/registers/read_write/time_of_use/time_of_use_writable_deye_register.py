from datetime import timedelta
from typing import Any, List, Optional

from time_of_use_charge import TimeOfUseCharge
from time_of_use_charges import TimeOfUseCharges
from time_of_use_data import TimeOfUseData
from time_of_use_powers import TimeOfUsePowers
from time_of_use_socs import TimeOfUseSocs
from time_of_use_time import TimeOfUseTime
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from time_of_use_times import TimeOfUseTimes
from time_of_use_week import TimeOfUseWeek
from time_of_use_weeks import TimeOfUseWeeks

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
    caching_time: Optional[timedelta] = None,
  ):
    super().__init__(
      address = 0,
      quantity = 0,
      name = name,
      description = description,
      suffix = suffix,
      avg = avg,
      caching_time = caching_time,
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
    charges_data = interactor.read_register(self.charge_address, self.items_count)
    times_data = interactor.read_register(self.time_address, self.items_count)
    powers_data = interactor.read_register(self.power_address, self.items_count)
    socs_data = interactor.read_register(self.soc_address, self.items_count)
    week_data = interactor.read_register(self.weekly_address, 1)[0]

    charges: List[TimeOfUseCharge] = []
    for charge in charges_data:
      charges.append(
        TimeOfUseCharge(
          grid_charge = bool(charge & 1),
          gen_charge = bool((charge >> 1) & 1),
          bit2 = bool((charge >> 2) & 1),
          bit3 = bool((charge >> 3) & 1),
          bit4 = bool((charge >> 4) & 1),
          bit5 = bool((charge >> 5) & 1),
          bit6 = bool((charge >> 6) & 1),
          bit7 = bool((charge >> 7) & 1),
        ))

    times: List[TimeOfUseTime] = []
    for time in times_data:
      # Ensure the number is 4 digits with leading zeros
      time_value = f"{time:04d}"

      # Extract hours and minutes
      times.append(TimeOfUseTime(
        hour = int(time_value[:2]),
        minute = int(time_value[-2:]),
      ))

    powers: List[int] = []
    for power in powers_data:
      powers.append(power)

    socs: List[int] = []
    for soc in socs_data:
      socs.append(soc)

    weeks = [
      TimeOfUseWeek(
        enabled = bool(week_data & (1 << 0)),
        monday = bool(week_data & (1 << 1)),
        tuesday = bool(week_data & (1 << 2)),
        wednesday = bool(week_data & (1 << 3)),
        thursday = bool(week_data & (1 << 4)),
        friday = bool(week_data & (1 << 5)),
        saturday = bool(week_data & (1 << 6)),
        sunday = bool(week_data & (1 << 7)),
      )
    ]

    data = TimeOfUseData(
      charges = TimeOfUseCharges(charges),
      times = TimeOfUseTimes(times),
      powers = TimeOfUsePowers(powers),
      socs = TimeOfUseSocs(socs),
      weeks = TimeOfUseWeeks(weeks),
    )

    try:
      # Just validate sizes
      data.validate(min_soc = 0, max_power = 7777777)
    except Exception as e:
      self.error(f'read(): {str(e)}')

    return data

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

    if value.charges.values:
      charges = [
        (int(charge.grid_charge) << 0) | #
        (int(charge.gen_charge) << 1) | #
        (int(charge.bit2) << 2) | #
        (int(charge.bit3) << 3) | #
        (int(charge.bit4) << 4) | #
        (int(charge.bit5) << 5) | #
        (int(charge.bit6) << 6) | #
        (int(charge.bit7) << 7) #
        for charge in value.charges.values
      ]

      if interactor.write_register(self.charge_address, charges) != len(charges):
        self.error(f'write(): something went wrong while writing charges in {self.description}')

    if value.times.values:
      times = [time.hour * 100 + time.minute for time in value.times.values]
      if interactor.write_register(self.time_address, times) != len(times):
        self.error(f'write(): something went wrong while writing times in {self.description}')

    if value.powers.values:
      if interactor.write_register(self.power_address, value.powers.values) != len(value.powers.values):
        self.error(f'write(): something went wrong while writing powers in {self.description}')

    if value.socs.values:
      if interactor.write_register(self.soc_address, value.socs.values) != len(value.socs.values):
        self.error(f'write(): something went wrong while writing socs in {self.description}')

    if value.weeks.values:
      weekly = ((int(value.week.enabled) << 0) | #
                (int(value.week.monday) << 1) | #
                (int(value.week.tuesday) << 2) | #
                (int(value.week.wednesday) << 3) | #
                (int(value.week.thursday) << 4) | #
                (int(value.week.friday) << 5) | #
                (int(value.week.saturday) << 6) | #
                (int(value.week.sunday) << 7) #
                )

      if interactor.write_register(self.weekly_address, [weekly]) != 1:
        self.error(f'write(): something went wrong while writing weekly in {self.description}')

    self._value = value
    return value
