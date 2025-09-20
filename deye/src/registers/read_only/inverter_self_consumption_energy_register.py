from typing import List

from deye_register import DeyeRegister
from base_deye_register import BaseDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType

class InverterSelfConsumptionEnergyRegister(BaseDeyeRegister):
  def __init__(self,
               pv_production_register: DeyeRegister,
               grid_purchased_energy_register: DeyeRegister,
               grid_feed_in_energy_register: DeyeRegister,
               battery_charged_energy_register: DeyeRegister,
               battery_discharged_energy_register: DeyeRegister,
               load_consumption_register: DeyeRegister,
               name: str,
               description: str,
               suffix: str,
               avg = DeyeRegisterAverageType.none):
    super().__init__(0, 0, name, description, suffix, avg)
    self._value = 0.0

    self._pv_production_register = pv_production_register
    self._grid_purchased_energy_register = grid_purchased_energy_register
    self._grid_feed_in_energy_register = grid_feed_in_energy_register
    self._battery_charged_energy_register = battery_charged_energy_register
    self._battery_discharged_energy_register = battery_discharged_energy_register
    self._load_consumption_register = load_consumption_register

  @property
  def addresses(self) -> List[int]:
    return self._pv_production_register.addresses +\
      self._grid_purchased_energy_register.addresses +\
      self._grid_feed_in_energy_register.addresses +\
      self._battery_charged_energy_register.addresses +\
      self._battery_discharged_energy_register.addresses +\
      self._load_consumption_register.addresses

  def enqueue(self, interactor: DeyeModbusInteractor):
    self._pv_production_register.enqueue(interactor)
    self._grid_purchased_energy_register.enqueue(interactor)
    self._grid_feed_in_energy_register.enqueue(interactor)
    self._battery_charged_energy_register.enqueue(interactor)
    self._battery_discharged_energy_register.enqueue(interactor)
    self._load_consumption_register.enqueue(interactor)

  def read(self, interactors: List[DeyeModbusInteractor]):
    self._pv_production_register.read(interactors)
    self._grid_purchased_energy_register.read(interactors)
    self._grid_feed_in_energy_register.read(interactors)
    self._battery_charged_energy_register.read(interactors)
    self._battery_discharged_energy_register.read(interactors)
    self._load_consumption_register.read(interactors)
    return super().read(interactors)

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = round(self._pv_production_register.value +\
      self._grid_purchased_energy_register.value -\
      self._grid_feed_in_energy_register.value -\
      self._battery_charged_energy_register.value +\
      self._battery_discharged_energy_register.value -\
      self._load_consumption_register.value, 1)

    return value
