import logging

from typing import List

from key_value_store import KeyValueStore
from ecoflow_device import EcoflowDevice
from ecoflow_devices import EcoflowDevices
from ecoflow_credentials import EcoflowCredentials
from ecoflow_powerstream_interactor import EcoflowPowerStreamInteractor

class EcoflowDeviceAggregator:
  """
  Aggregates multiple Ecoflow devices and manages their power settings
  through the Ecoflow API.

  This class maintains a cache of device power values and provides
  convenience methods to set, get, and adjust power across multiple devices.

  Parameters:
    cache_file (str): Path to a local file used for caching device power values.
    **kwargs: Optional keyword arguments passed to EcoflowPowerStreamInteractor:
      - name (str): Name identifier for logging (default: 'ecoflow').
      - verbose (bool): Enable verbose logging (default: False).
  """
  def __init__(self, cache_file, **kwargs):
    self.devices = EcoflowDevices()
    credentials = EcoflowCredentials()
    self.interactor = EcoflowPowerStreamInteractor(credentials, **kwargs)
    self.name = kwargs.get('name', 'ecoflow')
    self.verbose = kwargs.get('verbose', False)
    self.power_cache = KeyValueStore(cache_file, -1)
    self.logger = logging.getLogger()
    self.logger.setLevel(logging.INFO)

  @property
  def max_power(self) -> int:
    """
    Calculate the sum of the maximum configurable power of all devices.

    Returns:
      int: Sum of max_power across all devices.
    """
    return sum(device.max_power for device in self.devices.devices)

  @property
  def max_real_power(self) -> int:
    """
    Calculate the sum of the maximum real output power of all devices.

    Returns:
      int: Sum of max_real_power across all devices.
    """
    return sum(device.max_real_power for device in self.devices.devices)

  def reset_power_cache_for_offline_devices(self, online_devices: List[EcoflowDevice]):
    """
    Reset cached power values to -1 for all devices that are currently offline.

    This ensures that power values from offline devices do not interfere
    with calculations or attempts to set power.

    Args:
      online_devices (List[EcoflowDevice]): List of devices currently online.
    """
    online_serials = {device.serial for device in online_devices}
    for device in self.devices.devices:
      if device.serial not in online_serials:
        self.power_cache.set(device.serial, -1)

  def try_set_power(self, device: EcoflowDevice, power: int):
    """
    Attempt to set a new power value for a device, skipping the operation
    if the new value is identical to the cached value.

    Updates the device through the Ecoflow API via the interactor and
    writes the new power to the cache if changed.

    Args:
      device (EcoflowDevice): The device to set power for.
      power (int): Desired power in watts. Automatically clamped between
             0 and the device's max_power.
    """
    power = int(round(max(0, min(power, device.max_power))))

    if self.verbose:
      self.logger.info(f'{self.name}: setting power {power} W for {device.name}...')

    old_power = self.power_cache.get(device.serial)

    if self.verbose:
      self.logger.info(f'{self.name}: got power {old_power} W from cache for {device.name}')

    if old_power == power:
      if self.verbose:
        self.logger.info(f'{self.name}: new power ({power} W) for {device.name} is the same as old power. do nothing')
      return

    if self.verbose:
      self.logger.info(f'{self.name}: changing power for {device.name} to {power} W...')

    self.interactor.set_power(device, power)

    if self.verbose:
      self.logger.info(f'{self.name}: writing power {power} W to cache for {device.name}...')

    self.power_cache.set(device.serial, power)

  def get_cached_total_power(self) -> int:
    """
    Compute the total cached power across all devices.

    Ignores cached values <= 0 to avoid including offline or uninitialized devices.

    Returns:
      int: Sum of cached power values for all devices that have
         positive cached power.
    """
    total_power = 0
    for device in self.devices.devices:
      power = self.power_cache.get(device.serial)
      if power > 0:
        total_power += power

    return total_power

  def change_power(self, power_delta: int):
    """
    Adjust the total power of all online devices by a specified delta.

    The new total power is calculated as the sum of cached or retrieved
    power plus the delta, and then distributed evenly among online devices.

    Offline devices have their cache reset to -1 to prevent using
    outdated power values.

    Args:
      power_delta (int): Total change in power in watts. Can be positive
                 (increase) or negative (decrease).
    """
    online_devices = self.interactor.get_online_devices(self.devices)

    if not online_devices:
      if self.verbose:
        self.logger.info(f'{self.name}: no online devices for change_power()')
      return

    total_power = self.get_cached_total_power()

    if total_power < 0:
      total_power = 0
      for device in online_devices:
        total_power += self.interactor.get_power(device)

    power = int((total_power + power_delta) / len(online_devices))

    self.reset_power_cache_for_offline_devices(online_devices)

    for device in online_devices:
      self.try_set_power(device, power)

  def set_power(self, power: int):
    """
    Set a target total power across all online devices.

    The specified power is evenly distributed among online devices.
    Offline devices have their cache reset.

    Args:
      power (int): Total power to distribute among online devices in watts.
    """
    online_devices = self.interactor.get_online_devices(self.devices)

    if not online_devices:
      if self.verbose:
        self.logger.info(f'{self.name}: no online devices for set_power()')
      return

    power = int(power / len(online_devices))

    self.reset_power_cache_for_offline_devices(online_devices)

    for device in online_devices:
      self.try_set_power(device, power)

  def set_max_power(self):
    """
    Set each online device to its maximum configurable power.

    Offline devices have their cached power reset to prevent stale values.
    """
    online_devices = self.interactor.get_online_devices(self.devices)

    if not online_devices:
      if self.verbose:
        self.logger.info(f'{self.name}: no online devices for set_max_power()')
        self.reset_power_cache_for_offline_devices(online_devices)
      return

    self.reset_power_cache_for_offline_devices(online_devices)

    for device in online_devices:
      self.try_set_power(device, device.max_power)

  def get_power(self) -> int:
    """
    Retrieve the power output setting of all online devices.

    Queries each online device through the interactor and sums their
    current power output.

    Returns:
      int: Total power in watts across all online devices.
    """
    online_devices = self.interactor.get_online_devices(self.devices)

    if not online_devices:
      if self.verbose:
        self.logger.info(f'{self.name}: no online devices for get_power()')
      return 0

    return sum(self.interactor.get_power(device) for device in online_devices)
