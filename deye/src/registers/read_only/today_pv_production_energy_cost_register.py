from deye_register import DeyeRegister
from deye_register_average_type import DeyeRegisterAverageType
from today_energy_cost_base_register import TodayEnergyCostBaseRegister

class TodayPvProductionEnergyCostRegister(TodayEnergyCostBaseRegister):
  def __init__(
    self,
    pv_production_register: DeyeRegister,
    name: str,
    description: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(pv_production_register, name, description, avg)
