from typing import List

from deye_register import DeyeRegister
from deye_registers import DeyeRegisters
from deye_web_section import DeyeWebSection
from deye_web_base_info_section import DeyeWebBaseInfoSection

class DeyeWebBmsSection(DeyeWebBaseInfoSection):
  def __init__(self, registers: DeyeRegisters):
    super().__init__(
      DeyeWebSection.bms,
      only_master = True,
    )
    self._registers: List[DeyeRegister] = [
      registers.battery_soh_register,
      registers.battery_bms_charge_current_limit_register,
      registers.battery_bms_discharge_current_limit_register,
    ]
