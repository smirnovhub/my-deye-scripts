from deye_register import DeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from today_energy_cost_base_register import TodayEnergyCostBaseRegister

class TotalEnergyCostBaseRegister(TodayEnergyCostBaseRegister):
  def __init__(self,
               production_register: DeyeRegister,
               name: str,
               description: str,
               avg = DeyeRegisterAverageType.none):
    super().__init__(production_register, name, description, avg)

  def read_internal(self, interactor: DeyeModbusInteractor):
    total_cost = 0
    production = self.production_register.value

    for prod, cost in reversed(list(self.energy_cost.pv_energy_costs.items())):
      delta = production - prod
      total_cost += delta * cost
      production -= delta

    return total_cost
