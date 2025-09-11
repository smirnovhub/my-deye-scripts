from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class InverterSelfConsumptionPowerRegister(BaseDeyeRegister):
  def __init__(self, pv_total_power_register: DeyeRegister,
               grid_power_register: DeyeRegister, battery_power_register: DeyeRegister,
               load_power_register: DeyeRegister, name: str, description: str, suffix: str, avg = DeyeRegisterAverageType.none):
    super().__init__(0, 0, name, description, suffix, avg)

    self._pv_total_power_register = pv_total_power_register
    self._grid_power_register = grid_power_register
    self._battery_power_register = battery_power_register
    self._load_power_register = load_power_register

  @property
  def addresses(self):
    return self._pv_total_power_register.addresses +\
      self._grid_power_register.addresses +\
      self._battery_power_register.addresses +\
      self._load_power_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._pv_total_power_register.enqueue(interactor)
    self._grid_power_register.enqueue(interactor)
    self._battery_power_register.enqueue(interactor)
    self._load_power_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._pv_total_power_register.read(interactors)
    self._grid_power_register.read(interactors)
    self._battery_power_register.read(interactors)
    self._load_power_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = self._pv_total_power_register.value +\
      self._grid_power_register.value +\
      self._battery_power_register.value -\
      self._load_power_register.value

    return value
