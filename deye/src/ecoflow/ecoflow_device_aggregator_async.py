import logging

from typing import Dict, List
from datetime import datetime, timedelta

from ecoflow_device import EcoflowDevice
from ecoflow_devices import EcoflowDevices
from ecoflow_powerstream_interactor_async import EcoflowPowerStreamInteractorAsync

class EcoflowDeviceAggregatorAsync:
  """
  Aggregates multiple Ecoflow devices and manages their power settings
  through the Ecoflow API.

  This class maintains a cache of device power values and provides
  convenience methods to set, get, and adjust power across multiple devices.

  Parameters:
    access_key (str): Ecoflow API access key.
    secret_key (str): Ecoflow API secret key.
    cache_file (str): Path to a local file used for caching device power values.
    **kwargs: Optional keyword arguments passed to EcoflowPowerStreamInteractor:
      - name (str): Name identifier for logging (default: 'ecoflow').
      - verbose (bool): Enable verbose logging (default: False).
  """
  def __init__(
    self,
    access_key: str,
    secret_key: str,
    **kwargs,
  ):
    self._devices = EcoflowDevices()
    self._interactor = EcoflowPowerStreamInteractorAsync(
      access_key = access_key,
      secret_key = secret_key,
      **kwargs,
    )

    self._name = kwargs.get('name', 'ecoflow')
    self._verbose = kwargs.get('verbose', False)
    self._power_cache: Dict[str, int] = {}
    self._power_cache_last_update: Dict[str, datetime] = {}
    self._power_cache_reset_interval = timedelta(minutes = 5, seconds = 5)
    self._logger = logging.getLogger()
    self._logger.setLevel(logging.INFO)

  @property
  def max_power(self) -> int:
    """
    Calculate the sum of the maximum configurable power of all devices.

    Returns:
      int: Sum of max_power across all devices.
    """
    return sum(device.max_power for device in self._devices.devices)

  @property
  def max_real_power(self) -> int:
    """
    Calculate the sum of the maximum real output power of all devices.

    Returns:
      int: Sum of max_real_power across all devices.
    """
    return sum(device.max_real_power for device in self._devices.devices)

  async def reset_power_cache_for_offline_devices(self, online_devices: List[EcoflowDevice]):
    """
    Reset cached power values to -1 for all devices that are currently offline.

    This ensures that power values from offline devices do not interfere
    with calculations or attempts to set power.

    Args:
      online_devices (List[EcoflowDevice]): List of devices currently online.
    """
    online_serials = {device.serial for device in online_devices}
    for device in self._devices.devices:
      if device.serial not in online_serials:
        self._set_cached_power(device, -1)

  async def try_set_power(self, device: EcoflowDevice, power: int):
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

    if self._verbose:
      self._logger.info(f'{self._name}: setting power {power} W for {device.name}...')

    old_power = self._get_cached_power(device)

    if self._verbose:
      self._logger.info(f'{self._name}: got power {old_power} W from cache for {device.name}')

    if old_power == power:
      if self._verbose:
        self._logger.info(f'{self._name}: new power ({power} W) for {device.name} is the same as old power. do nothing')
      return

    if self._verbose:
      self._logger.info(f'{self._name}: changing power for {device.name} to {power} W...')

    await self._interactor.set_power(device, power)

    if self._verbose:
      self._logger.info(f'{self._name}: writing power {power} W to cache for {device.name}...')

    self._set_cached_power(device, power)

  async def get_cached_total_power(self) -> int:
    """
    Compute the total cached power across all devices.

    Ignores cached values <= 0 to avoid including offline or uninitialized devices.

    Returns:
      int: Sum of cached power values for all devices that have
         positive cached power.
    """
    total_power = 0
    for device in self._devices.devices:
      power = self._get_cached_power(device)
      if power > 0:
        total_power += power

    return total_power

  async def change_power(self, power_delta: int):
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
    online_devices = await self._interactor.get_online_devices(self._devices)

    if not online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for change_power()')
      return

    total_power = await self.get_cached_total_power()

    if total_power < 0:
      total_power = 0
      for device in online_devices:
        total_power += await self._interactor.get_power(device)

    power = int((total_power + power_delta) / len(online_devices))

    await self.reset_power_cache_for_offline_devices(online_devices)

    for device in online_devices:
      await self.try_set_power(device, power)

  async def set_power(self, power: int):
    """
    Set a target total power across all online devices.

    The specified power is evenly distributed among online devices.
    Offline devices have their cache reset.

    Args:
      power (int): Total power to distribute among online devices in watts.
    """
    online_devices = await self._interactor.get_online_devices(self._devices)

    if not online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for set_power()')
      return

    power = int(power / len(online_devices))

    await self.reset_power_cache_for_offline_devices(online_devices)

    for device in online_devices:
      await self.try_set_power(device, power)

  async def set_max_power(self):
    """
    Set each online device to its maximum configurable power.

    Offline devices have their cached power reset to prevent stale values.
    """
    online_devices = await self._interactor.get_online_devices(self._devices)

    if not online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for set_max_power()')
        await self.reset_power_cache_for_offline_devices(online_devices)
      return

    await self.reset_power_cache_for_offline_devices(online_devices)

    for device in online_devices:
      await self.try_set_power(device, device.max_power)

  async def get_power(self) -> int:
    """
    Retrieve the power output setting of all online devices.

    Queries each online device through the interactor and sums their
    current power output.

    Returns:
      int: Total power in watts across all online devices.
    """
    online_devices = await self._interactor.get_online_devices(self._devices)

    if not online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for get_power()')
      return 0

    powers = [await self._interactor.get_power(device) for device in online_devices]

    return sum(powers)

  def _get_cached_power(self, device: EcoflowDevice) -> int:
    last_update = self._power_cache_last_update.get(device.serial, datetime.min)
    if datetime.now() - last_update > self._power_cache_reset_interval:
      self._power_cache[device.serial] = -1
      self._power_cache_last_update[device.serial] = datetime.now()
      self._logger.info(f"Cached power for {device.name} has been reset.")
    return self._power_cache.get(device.serial, -1)

  def _set_cached_power(self, device: EcoflowDevice, power: int) -> None:
    self._power_cache[device.serial] = power
    self._power_cache_last_update[device.serial] = datetime.now()
