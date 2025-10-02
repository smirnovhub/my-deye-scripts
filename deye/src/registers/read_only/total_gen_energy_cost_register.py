from deye_register import DeyeRegister
from deye_register_average_type import DeyeRegisterAverageType
from total_energy_cost_base_register import TotalEnergyCostBaseRegister

class TotalGenEnergyCostRegister(TotalEnergyCostBaseRegister):
  def __init__(
    self,
    gen_energy_register: DeyeRegister,
    name: str,
    description: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(gen_energy_register, name, description, avg)
