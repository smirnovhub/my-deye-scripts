from typing import Dict
from datetime import timedelta
from dataclasses import dataclass

# Define register caching class
@dataclass
class CachedDeyeRegister:
  address: int
  description: str
  caching_time: timedelta

# Define caching time constants in seconds
CACHE_STATIC = timedelta(hours = 24)
CACHE_CONFIG = timedelta(minutes = 30)

# Initialize mapping of all Deye registers to their cache settings
deye_registers_caching_time: Dict[int, CachedDeyeRegister] = {
  # Hardware and basic info block
  3: CachedDeyeRegister(address = 3, description = "Serial number byte 1-2", caching_time = CACHE_STATIC),
  4: CachedDeyeRegister(address = 4, description = "Serial number byte 3-4", caching_time = CACHE_STATIC),
  5: CachedDeyeRegister(address = 5, description = "Serial number byte 5-6", caching_time = CACHE_STATIC),
  6: CachedDeyeRegister(address = 6, description = "Serial number byte 7-8", caching_time = CACHE_STATIC),
  7: CachedDeyeRegister(address = 7, description = "Serial number byte 9-10", caching_time = CACHE_STATIC),
  8: CachedDeyeRegister(address = 8, description = "Rated power", caching_time = CACHE_STATIC),
  9: CachedDeyeRegister(address = 9, description = "Chip type", caching_time = CACHE_STATIC),
  10: CachedDeyeRegister(address = 10, description = "Comm board FW ver 2", caching_time = CACHE_STATIC),
  11: CachedDeyeRegister(address = 11, description = "Ctrl board aux program ver", caching_time = CACHE_STATIC),
  12: CachedDeyeRegister(address = 12, description = "Ctrl board FW ver 2", caching_time = CACHE_STATIC),
  13: CachedDeyeRegister(address = 13, description = "Ctrl board FW ver", caching_time = CACHE_STATIC),
  14: CachedDeyeRegister(address = 14, description = "Comm board FW ver", caching_time = CACHE_STATIC),
  15: CachedDeyeRegister(address = 15, description = "Safety type", caching_time = CACHE_STATIC),
  16: CachedDeyeRegister(address = 16, description = "Inverter nominal power low word", caching_time = CACHE_STATIC),
  17: CachedDeyeRegister(address = 17, description = "Inverter nominal power high word", caching_time = CACHE_STATIC),
  18: CachedDeyeRegister(address = 18, description = "Phases and MPPT count", caching_time = CACHE_STATIC),
  19: CachedDeyeRegister(address = 19, description = "Nominal grid voltage", caching_time = CACHE_STATIC),

  # System limits and changeable configurations
  20: CachedDeyeRegister(address = 20, description = "Remote Lock", caching_time = CACHE_CONFIG),
  21: CachedDeyeRegister(address = 21, description = "Self-check time", caching_time = CACHE_CONFIG),
  25: CachedDeyeRegister(address = 25, description = "RISO low limit and external CT flag", caching_time = CACHE_CONFIG),
  26: CachedDeyeRegister(address = 26, description = "DC voltage upper limit", caching_time = CACHE_CONFIG),
  27: CachedDeyeRegister(address = 27, description = "Grid voltage upper limit", caching_time = CACHE_CONFIG),
  28: CachedDeyeRegister(address = 28, description = "ATS, low power, MPPT settings", caching_time = CACHE_CONFIG),
  29: CachedDeyeRegister(address = 29, description = "Grid frequency upper limit", caching_time = CACHE_CONFIG),
  30: CachedDeyeRegister(address = 30, description = "Grid frequency lower limit", caching_time = CACHE_CONFIG),
  31: CachedDeyeRegister(address = 31, description = "Grid current upper limit", caching_time = CACHE_CONFIG),
  32: CachedDeyeRegister(address = 32, description = "Startup voltage upper limit", caching_time = CACHE_CONFIG),
  33: CachedDeyeRegister(address = 33, description = "Startup voltage lower limit", caching_time = CACHE_CONFIG),
  34: CachedDeyeRegister(address = 34, description = "Low Noise Mode", caching_time = CACHE_CONFIG),
  35: CachedDeyeRegister(address = 35, description = "Over-frequency derating", caching_time = CACHE_CONFIG),
  36: CachedDeyeRegister(address = 36, description = "Import power limiter", caching_time = CACHE_CONFIG),
  37: CachedDeyeRegister(address = 37, description = "Communication address", caching_time = CACHE_STATIC),
  38: CachedDeyeRegister(address = 38, description = "Communication baud rate", caching_time = CACHE_STATIC),

  # Advanced grid and protection settings
  46: CachedDeyeRegister(address = 46, description = "Absorption charge time enable", caching_time = CACHE_CONFIG),
  47: CachedDeyeRegister(address = 47, description = "MPPT count and soft start", caching_time = CACHE_CONFIG),
  48: CachedDeyeRegister(address = 48, description = "CEI self-check enable", caching_time = CACHE_CONFIG),
  49: CachedDeyeRegister(address = 49, description = "RCD and freq derating enable", caching_time = CACHE_CONFIG),
  50: CachedDeyeRegister(address = 50, description = "RISO control enable", caching_time = CACHE_CONFIG),
  51: CachedDeyeRegister(address = 51, description = "Grid standard", caching_time = CACHE_CONFIG),
  52: CachedDeyeRegister(address = 52, description = "Ext CT ratio and Max PV power", caching_time = CACHE_CONFIG),
  53: CachedDeyeRegister(address = 53, description = "Hardware matching", caching_time = CACHE_CONFIG),
  54: CachedDeyeRegister(address = 54, description = "AC power ratio", caching_time = CACHE_CONFIG),
  56: CachedDeyeRegister(address = 56, description = "Limiter function enable", caching_time = CACHE_CONFIG),
  57: CachedDeyeRegister(address = 57, description = "Energy gen factor and RSD enable", caching_time = CACHE_CONFIG),
  58: CachedDeyeRegister(address = 58, description = "General settings bit flags", caching_time = CACHE_CONFIG),

  # Hybrid battery and generator configurations
  200: CachedDeyeRegister(address = 200, description = "Battery type", caching_time = CACHE_CONFIG),
  201: CachedDeyeRegister(address = 201, description = "Equalization voltage", caching_time = CACHE_CONFIG),
  202: CachedDeyeRegister(address = 202, description = "Absorption voltage", caching_time = CACHE_CONFIG),
  203: CachedDeyeRegister(address = 203, description = "Float voltage", caching_time = CACHE_CONFIG),
  204: CachedDeyeRegister(address = 204, description = "Battery capacity", caching_time = CACHE_CONFIG),
  205: CachedDeyeRegister(address = 205, description = "Empty voltage threshold", caching_time = CACHE_CONFIG),
  206: CachedDeyeRegister(address = 206, description = "ZeroExport min power", caching_time = CACHE_CONFIG),
  207: CachedDeyeRegister(address = 207, description = "Equalization cycle days", caching_time = CACHE_CONFIG),
  208: CachedDeyeRegister(address = 208, description = "Equalization duration", caching_time = CACHE_CONFIG),
  209: CachedDeyeRegister(address = 209, description = "TEMPCO factor", caching_time = CACHE_CONFIG),
  # 210: CacheDeyeRegister(address = 210, description = "Max charge current", caching_time = CACHE_CONFIG),
  211: CachedDeyeRegister(address = 211, description = "Max discharge current", caching_time = CACHE_CONFIG),
  212: CachedDeyeRegister(address = 212, description = "Reserved config", caching_time = CACHE_CONFIG),
  213: CachedDeyeRegister(address = 213, description = "Battery work mode", caching_time = CACHE_CONFIG),
  215: CachedDeyeRegister(address = 215, description = "Battery internal resistance", caching_time = CACHE_CONFIG),
  216: CachedDeyeRegister(address = 216, description = "Battery charge efficiency", caching_time = CACHE_CONFIG),
  217: CachedDeyeRegister(address = 217, description = "ShutDown capacity percent", caching_time = CACHE_CONFIG),
  218: CachedDeyeRegister(address = 218, description = "Restart capacity percent", caching_time = CACHE_CONFIG),
  219: CachedDeyeRegister(address = 219, description = "LowBatt capacity percent", caching_time = CACHE_CONFIG),
  220: CachedDeyeRegister(address = 220, description = "ShutDown voltage", caching_time = CACHE_CONFIG),
  221: CachedDeyeRegister(address = 221, description = "Restart voltage", caching_time = CACHE_CONFIG),
  222: CachedDeyeRegister(address = 222, description = "LowBatt voltage", caching_time = CACHE_CONFIG),
  223: CachedDeyeRegister(address = 223, description = "Max generator run time", caching_time = CACHE_CONFIG),
  224: CachedDeyeRegister(address = 224, description = "Generator cooldown time", caching_time = CACHE_CONFIG),
  225: CachedDeyeRegister(address = 225, description = "Gen start voltage", caching_time = CACHE_CONFIG),
  226: CachedDeyeRegister(address = 226, description = "Gen start capacity", caching_time = CACHE_CONFIG),
  227: CachedDeyeRegister(address = 227, description = "Gen charge current", caching_time = CACHE_CONFIG),
  228: CachedDeyeRegister(address = 228, description = "Grid charge start voltage", caching_time = CACHE_CONFIG),
  229: CachedDeyeRegister(address = 229, description = "Grid charge start capacity", caching_time = CACHE_CONFIG),
  230: CachedDeyeRegister(address = 230, description = "Grid charge current", caching_time = CACHE_CONFIG),
  231: CachedDeyeRegister(address = 231, description = "Gen charge enable", caching_time = CACHE_CONFIG),
  232: CachedDeyeRegister(address = 232, description = "Grid charge enable", caching_time = CACHE_CONFIG),
  233: CachedDeyeRegister(address = 233, description = "Solar input as PSU", caching_time = CACHE_CONFIG),
  234: CachedDeyeRegister(address = 234, description = "Force Gen as load", caching_time = CACHE_CONFIG),
  235: CachedDeyeRegister(address = 235, description = "Gen port mode", caching_time = CACHE_CONFIG),
  236: CachedDeyeRegister(address = 236, description = "SmartLoad OFF voltage", caching_time = CACHE_CONFIG),
  237: CachedDeyeRegister(address = 237, description = "SmartLoad OFF capacity", caching_time = CACHE_CONFIG),
  238: CachedDeyeRegister(address = 238, description = "SmartLoad ON voltage", caching_time = CACHE_CONFIG),
  239: CachedDeyeRegister(address = 239, description = "SmartLoad ON capacity", caching_time = CACHE_CONFIG),
  240: CachedDeyeRegister(address = 240, description = "Min Solar for Gen start", caching_time = CACHE_CONFIG),
  242: CachedDeyeRegister(address = 242, description = "Gen Grid Signal On", caching_time = CACHE_CONFIG),
  243: CachedDeyeRegister(address = 243, description = "Energy management mode", caching_time = CACHE_CONFIG),
  244: CachedDeyeRegister(address = 244, description = "Limiter control enable", caching_time = CACHE_CONFIG),
  245: CachedDeyeRegister(address = 245, description = "Export power limiter", caching_time = CACHE_CONFIG),
  246: CachedDeyeRegister(address = 246, description = "Ext CT phase and direction", caching_time = CACHE_CONFIG),
  247: CachedDeyeRegister(address = 247, description = "Solar sell enable", caching_time = CACHE_CONFIG),
  248: CachedDeyeRegister(address = 248, description = "Time of use sell enable", caching_time = CACHE_CONFIG),
  249: CachedDeyeRegister(address = 249, description = "Reserved settings", caching_time = CACHE_CONFIG),

  # Grid protection timings
  312: CachedDeyeRegister(address = 312, description = "Grid V low limit time stage 2", caching_time = CACHE_CONFIG),
  313: CachedDeyeRegister(address = 313, description = "Grid V low limit time stage 3", caching_time = CACHE_CONFIG),
  314: CachedDeyeRegister(address = 314, description = "Grid Freq high limit time stage 1", caching_time = CACHE_CONFIG),
  315: CachedDeyeRegister(address = 315, description = "Grid Freq high limit time stage 2", caching_time = CACHE_CONFIG),
  316: CachedDeyeRegister(address = 316, description = "Grid Freq high limit time stage 3", caching_time = CACHE_CONFIG),
  317: CachedDeyeRegister(address = 317, description = "Grid Freq low limit time stage 1", caching_time = CACHE_CONFIG),
  318: CachedDeyeRegister(address = 318, description = "Grid Freq low limit time stage 2", caching_time = CACHE_CONFIG),
  319: CachedDeyeRegister(address = 319, description = "Grid Freq low limit time stage 3", caching_time = CACHE_CONFIG),
}
