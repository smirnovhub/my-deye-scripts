from typing import Dict
from datetime import timedelta
from dataclasses import dataclass
from deye_registers import DeyeRegisters
from src.deye_proxy_config import DeyeProxyConfig

# Define register caching metadata class
@dataclass
class CachedDeyeRegister:
  desc: str
  caching_time: timedelta

# Define standard caching time constants
CACHE_STATIC = timedelta(hours = 24)
CACHE_CONFIG = timedelta(minutes = 30)

# Explicit mapping of specific Deye registers to their cache settings
EXPLICIT_DEYE_REGISTERS_CACHE: Dict[int, CachedDeyeRegister] = {
  # Hardware and basic info block
  3: CachedDeyeRegister(desc = "Serial number byte 1-2", caching_time = CACHE_STATIC),
  4: CachedDeyeRegister(desc = "Serial number byte 3-4", caching_time = CACHE_STATIC),
  5: CachedDeyeRegister(desc = "Serial number byte 5-6", caching_time = CACHE_STATIC),
  6: CachedDeyeRegister(desc = "Serial number byte 7-8", caching_time = CACHE_STATIC),
  7: CachedDeyeRegister(desc = "Serial number byte 9-10", caching_time = CACHE_STATIC),
  8: CachedDeyeRegister(desc = "Rated power", caching_time = CACHE_STATIC),
  9: CachedDeyeRegister(desc = "Chip type", caching_time = CACHE_STATIC),
  10: CachedDeyeRegister(desc = "Comm board FW ver 2", caching_time = CACHE_STATIC),
  11: CachedDeyeRegister(desc = "Ctrl board aux program ver", caching_time = CACHE_STATIC),
  12: CachedDeyeRegister(desc = "Ctrl board FW ver 2", caching_time = CACHE_STATIC),
  13: CachedDeyeRegister(desc = "Ctrl board FW ver", caching_time = CACHE_STATIC),
  14: CachedDeyeRegister(desc = "Comm board FW ver", caching_time = CACHE_STATIC),
  15: CachedDeyeRegister(desc = "Safety type", caching_time = CACHE_STATIC),
  16: CachedDeyeRegister(desc = "Inverter nominal power low word", caching_time = CACHE_STATIC),
  17: CachedDeyeRegister(desc = "Inverter nominal power high word", caching_time = CACHE_STATIC),
  18: CachedDeyeRegister(desc = "Phases and MPPT count", caching_time = CACHE_STATIC),
  19: CachedDeyeRegister(desc = "Nominal grid voltage", caching_time = CACHE_STATIC),

  # System limits and changeable configurations
  20: CachedDeyeRegister(desc = "Remote Lock", caching_time = CACHE_CONFIG),
  21: CachedDeyeRegister(desc = "Self-check time", caching_time = CACHE_CONFIG),
  25: CachedDeyeRegister(desc = "RISO low limit and external CT flag", caching_time = CACHE_CONFIG),
  26: CachedDeyeRegister(desc = "DC voltage upper limit", caching_time = CACHE_CONFIG),
  27: CachedDeyeRegister(desc = "Grid voltage upper limit", caching_time = CACHE_CONFIG),
  28: CachedDeyeRegister(desc = "ATS, low power, MPPT settings", caching_time = CACHE_CONFIG),
  29: CachedDeyeRegister(desc = "Grid frequency upper limit", caching_time = CACHE_CONFIG),
  30: CachedDeyeRegister(desc = "Grid frequency lower limit", caching_time = CACHE_CONFIG),
  31: CachedDeyeRegister(desc = "Grid current upper limit", caching_time = CACHE_CONFIG),
  32: CachedDeyeRegister(desc = "Startup voltage upper limit", caching_time = CACHE_CONFIG),
  33: CachedDeyeRegister(desc = "Startup voltage lower limit", caching_time = CACHE_CONFIG),
  34: CachedDeyeRegister(desc = "Low Noise Mode", caching_time = CACHE_CONFIG),
  35: CachedDeyeRegister(desc = "Over-frequency derating", caching_time = CACHE_CONFIG),
  36: CachedDeyeRegister(desc = "Import power limiter", caching_time = CACHE_CONFIG),
  37: CachedDeyeRegister(desc = "Communication address", caching_time = CACHE_STATIC),
  38: CachedDeyeRegister(desc = "Communication baud rate", caching_time = CACHE_STATIC),
  39: CachedDeyeRegister(desc = "Power factor regulation", caching_time = CACHE_CONFIG),
  40: CachedDeyeRegister(desc = "Active power regulation", caching_time = CACHE_CONFIG),
  41: CachedDeyeRegister(desc = "Reactive power regulation", caching_time = CACHE_CONFIG),
  42: CachedDeyeRegister(desc = "Apparent power regulation", caching_time = CACHE_CONFIG),
  43: CachedDeyeRegister(desc = "Switch on and off enable", caching_time = CACHE_CONFIG),
  44: CachedDeyeRegister(desc = "Factory reset enable", caching_time = CACHE_CONFIG),
  45: CachedDeyeRegister(desc = "Self-checking time", caching_time = CACHE_CONFIG),

  # Advanced grid and protection settings
  46: CachedDeyeRegister(desc = "Absorption charge time enable", caching_time = CACHE_CONFIG),
  47: CachedDeyeRegister(desc = "MPPT count and soft start", caching_time = CACHE_CONFIG),
  48: CachedDeyeRegister(desc = "CEI self-check enable", caching_time = CACHE_CONFIG),
  49: CachedDeyeRegister(desc = "RCD and freq derating enable", caching_time = CACHE_CONFIG),
  50: CachedDeyeRegister(desc = "RISO control enable", caching_time = CACHE_CONFIG),
  51: CachedDeyeRegister(desc = "Grid standard", caching_time = CACHE_CONFIG),
  52: CachedDeyeRegister(desc = "Ext CT ratio and Max PV power", caching_time = CACHE_CONFIG),
  53: CachedDeyeRegister(desc = "Hardware matching", caching_time = CACHE_CONFIG),
  54: CachedDeyeRegister(desc = "AC power ratio", caching_time = CACHE_CONFIG),
  55: CachedDeyeRegister(desc = "Factory test instruction 1", caching_time = CACHE_CONFIG),
  56: CachedDeyeRegister(desc = "Limiter function enable", caching_time = CACHE_CONFIG),
  57: CachedDeyeRegister(desc = "Energy gen factor and RSD enable", caching_time = CACHE_CONFIG),
  58: CachedDeyeRegister(desc = "General settings bit flags", caching_time = CACHE_CONFIG),

  # Hybrid battery and generator configurations
  200: CachedDeyeRegister(desc = "Battery type", caching_time = CACHE_CONFIG),
  201: CachedDeyeRegister(desc = "Equalization voltage", caching_time = CACHE_CONFIG),
  202: CachedDeyeRegister(desc = "Absorption voltage", caching_time = CACHE_CONFIG),
  203: CachedDeyeRegister(desc = "Float voltage", caching_time = CACHE_CONFIG),
  204: CachedDeyeRegister(desc = "Battery capacity", caching_time = CACHE_CONFIG),
  205: CachedDeyeRegister(desc = "Empty voltage threshold", caching_time = CACHE_CONFIG),
  206: CachedDeyeRegister(desc = "ZeroExport min power", caching_time = CACHE_CONFIG),
  207: CachedDeyeRegister(desc = "Equalization cycle days", caching_time = CACHE_CONFIG),
  208: CachedDeyeRegister(desc = "Equalization duration", caching_time = CACHE_CONFIG),
  209: CachedDeyeRegister(desc = "TEMPCO factor", caching_time = CACHE_CONFIG),
  # 210: CachedDeyeRegister(description = "Max charge current", caching_time = CACHE_CONFIG),
  211: CachedDeyeRegister(desc = "Max discharge current", caching_time = CACHE_CONFIG),
  212: CachedDeyeRegister(desc = "Reserved config", caching_time = CACHE_CONFIG),
  213: CachedDeyeRegister(desc = "Battery work mode", caching_time = CACHE_CONFIG),
  214: CachedDeyeRegister(desc = "Lithium battery wake up enable", caching_time = CACHE_CONFIG),
  215: CachedDeyeRegister(desc = "Battery internal resistance", caching_time = CACHE_CONFIG),
  216: CachedDeyeRegister(desc = "Battery charge efficiency", caching_time = CACHE_CONFIG),
  217: CachedDeyeRegister(desc = "ShutDown capacity percent", caching_time = CACHE_CONFIG),
  218: CachedDeyeRegister(desc = "Restart capacity percent", caching_time = CACHE_CONFIG),
  219: CachedDeyeRegister(desc = "LowBatt capacity percent", caching_time = CACHE_CONFIG),
  220: CachedDeyeRegister(desc = "ShutDown voltage", caching_time = CACHE_CONFIG),
  221: CachedDeyeRegister(desc = "Restart voltage", caching_time = CACHE_CONFIG),
  222: CachedDeyeRegister(desc = "LowBatt voltage", caching_time = CACHE_CONFIG),
  223: CachedDeyeRegister(desc = "Max generator run time", caching_time = CACHE_CONFIG),
  224: CachedDeyeRegister(desc = "Generator cooldown time", caching_time = CACHE_CONFIG),
  225: CachedDeyeRegister(desc = "Gen start voltage", caching_time = CACHE_CONFIG),
  226: CachedDeyeRegister(desc = "Gen start capacity", caching_time = CACHE_CONFIG),
  227: CachedDeyeRegister(desc = "Gen charge current", caching_time = CACHE_CONFIG),
  228: CachedDeyeRegister(desc = "Grid charge start voltage", caching_time = CACHE_CONFIG),
  229: CachedDeyeRegister(desc = "Grid charge start capacity", caching_time = CACHE_CONFIG),
  230: CachedDeyeRegister(desc = "Grid charge current", caching_time = CACHE_CONFIG),
  231: CachedDeyeRegister(desc = "Gen charge enable", caching_time = CACHE_CONFIG),
  232: CachedDeyeRegister(desc = "Grid charge enable", caching_time = CACHE_CONFIG),
  233: CachedDeyeRegister(desc = "Solar input as PSU", caching_time = CACHE_CONFIG),
  234: CachedDeyeRegister(desc = "Force Gen as load", caching_time = CACHE_CONFIG),
  235: CachedDeyeRegister(desc = "Gen port mode", caching_time = CACHE_CONFIG),
  236: CachedDeyeRegister(desc = "SmartLoad OFF voltage", caching_time = CACHE_CONFIG),
  237: CachedDeyeRegister(desc = "SmartLoad OFF capacity", caching_time = CACHE_CONFIG),
  238: CachedDeyeRegister(desc = "SmartLoad ON voltage", caching_time = CACHE_CONFIG),
  239: CachedDeyeRegister(desc = "SmartLoad ON capacity", caching_time = CACHE_CONFIG),
  240: CachedDeyeRegister(desc = "Min Solar for Gen start", caching_time = CACHE_CONFIG),
  241: CachedDeyeRegister(desc = "Min solar for generator and PWM test enable", caching_time = CACHE_CONFIG),
  242: CachedDeyeRegister(desc = "Gen Grid Signal On", caching_time = CACHE_CONFIG),
  243: CachedDeyeRegister(desc = "Energy management mode", caching_time = CACHE_CONFIG),
  244: CachedDeyeRegister(desc = "Limiter control enable", caching_time = CACHE_CONFIG),
  245: CachedDeyeRegister(desc = "Export power limiter", caching_time = CACHE_CONFIG),
  246: CachedDeyeRegister(desc = "Ext CT phase and direction", caching_time = CACHE_CONFIG),
  247: CachedDeyeRegister(desc = "Solar sell enable", caching_time = CACHE_CONFIG),
  248: CachedDeyeRegister(desc = "Time of use sell enable", caching_time = CACHE_CONFIG),
  249: CachedDeyeRegister(desc = "Reserved settings", caching_time = CACHE_CONFIG),

  # Grid protection timings
  312: CachedDeyeRegister(desc = "Grid V low limit time stage 2", caching_time = CACHE_CONFIG),
  313: CachedDeyeRegister(desc = "Grid V low limit time stage 3", caching_time = CACHE_CONFIG),
  314: CachedDeyeRegister(desc = "Grid Freq high limit time stage 1", caching_time = CACHE_CONFIG),
  315: CachedDeyeRegister(desc = "Grid Freq high limit time stage 2", caching_time = CACHE_CONFIG),
  316: CachedDeyeRegister(desc = "Grid Freq high limit time stage 3", caching_time = CACHE_CONFIG),
  317: CachedDeyeRegister(desc = "Grid Freq low limit time stage 1", caching_time = CACHE_CONFIG),
  318: CachedDeyeRegister(desc = "Grid Freq low limit time stage 2", caching_time = CACHE_CONFIG),
  319: CachedDeyeRegister(desc = "Grid Freq low limit time stage 3", caching_time = CACHE_CONFIG),
}

class DeyeRegistersCachingTimeHolder:
  """
  Provides pre-calculated caching intervals in seconds for Deye register addresses in O(1) time complexity.
  """
  def __init__(
    self,
    config: DeyeProxyConfig,
  ) -> None:
    self._config = config
    self._caching_times_by_address: Dict[int, int] = {}

    registers = DeyeRegisters()

    # Populate caching time map from dynamic register definitions if provided
    for register in registers.all_registers:
      caching_time = register.caching_time
      if caching_time:
        seconds = round(caching_time.total_seconds())
        for address in register.addresses:
          self._caching_times_by_address[address] = seconds

    # Override or enrich with explicitly specified register caching rules
    for address, register in EXPLICIT_DEYE_REGISTERS_CACHE.items():
      self._caching_times_by_address[address] = round(register.caching_time.total_seconds())

  def get_caching_time(self, address: int) -> int:
    """
    Retrieve caching time in seconds for a specific register address using O(1) dictionary lookup.
    """
    return self._caching_times_by_address.get(address, self._config.CACHE_UPDATE_INTERVAL)
