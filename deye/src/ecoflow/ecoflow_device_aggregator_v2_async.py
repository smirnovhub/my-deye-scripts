import random
import logging

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ecoflow_device import EcoflowDevice
from ecoflow_devices import EcoflowDevices
from ecoflow_powerstream_interactor_async import EcoflowPowerStreamInteractorAsync

class EcoflowDeviceAggregatorV2Async:
  """
  Aggregates multiple Ecoflow devices and manages their power settings
  through the Ecoflow API.

  This class maintains a cache of device power values and provides
  convenience methods to set, get, and adjust power across multiple devices.

  Parameters:
    access_key (str): Ecoflow API access key.
    secret_key (str): Ecoflow API secret key.
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
    self._power_cache_update_interval = timedelta(minutes = 10)
    self._logger = logging.getLogger()

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

  async def _try_set_power(self, device: EcoflowDevice, power: int):
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
    await self._update_cached_power_for_one_device_at_once(self._devices.devices)

    total_power = 0
    for device in self._devices.devices:
      power = self._get_cached_power(device)
      if power > 0:
        total_power += power

    return total_power

  def _get_device_with_min_power(self, devices: List[EcoflowDevice]) -> Optional[EcoflowDevice]:
    """
    Find an online device with the lowest cached power.
    If multiple devices have the same minimum power, one is chosen at random.
    """
    if not devices:
      return None

    # Track device serials and their corresponding cached power values
    device_powers: Dict[str, int] = {}
    for dev in devices:
      device_powers[dev.serial] = self._get_cached_power(dev)

    # Find the minimum power value among all devices
    min_power = min(device_powers.values())

    # Collect all devices that share this minimum power value
    candidates = [d for d in devices if device_powers[d.serial] == min_power]

    # Select a random device from the candidates
    return random.choice(candidates)

  def _get_device_with_max_power(self, devices: List[EcoflowDevice]) -> Optional[EcoflowDevice]:
    """
    Find an online device with the highest cached power.
    If multiple devices have the same maximum power, one is chosen at random.
    """
    if not devices:
      return None

    # Track device serials and their corresponding cached power values
    device_powers: Dict[str, int] = {}
    for dev in devices:
      device_powers[dev.serial] = self._get_cached_power(dev)

    # Find the maximum power value among all devices
    max_power = max(device_powers.values())

    # Collect all devices that share this maximum power value
    candidates = [d for d in devices if device_powers[d.serial] == max_power]

    # Select a random device from the candidates
    return random.choice(candidates)

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
    if abs(power_delta) < 5:
      self._logger.warning(f'{self._name}: power_delta is too low in change_power()')
      return

    online_devices = await self._interactor.get_online_devices(self._devices)

    if not online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for change_power()')
        await self.reset_power_cache_for_offline_devices(online_devices)
      return

    await self.reset_power_cache_for_offline_devices(online_devices)

    if power_delta > 0:
      device = self._get_device_with_min_power(online_devices)
    else:
      device = self._get_device_with_max_power(online_devices)

    if not device:
      self._logger.warning(f"{self._name}: can't get device in change_power()")
      return

    if self._need_update_cached_power(device):
      await self._update_cached_power(device)

    power = self._get_cached_power(device)
    await self._try_set_power(device, power + power_delta)

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

    device = self._get_device_with_min_power(online_devices)
    if not device:
      self._logger.warning(f"{self._name}: can't get device in set_max_power()")
      return

    if self._need_update_cached_power(device):
      await self._update_cached_power(device)

    await self._try_set_power(device, device.max_power)

  def _get_cached_power(self, device: EcoflowDevice) -> int:
    return self._power_cache.get(device.serial, -1)

  def _set_cached_power(self, device: EcoflowDevice, power: int) -> None:
    self._power_cache[device.serial] = power
    self._power_cache_last_update[device.serial] = datetime.now()
    self._logger.info(f"Cached power last update time for {device.name} has been updated.")

  def _need_update_cached_power(self, device: EcoflowDevice) -> bool:
    last_update = self._power_cache_last_update.get(device.serial, datetime.min)
    return datetime.now() - last_update > self._power_cache_update_interval

  async def _update_cached_power(self, device: EcoflowDevice) -> None:
    power = await self._interactor.get_power(device)
    self._power_cache[device.serial] = power
    self._power_cache_last_update[device.serial] = datetime.now()
    self._logger.info(f"Cached power for {device.name} has been updated to {power} W.")

  async def _update_cached_power_for_one_device_at_once(self, devices: List[EcoflowDevice]) -> None:
    """
    Find and update the cache via API for strictly the first device that requires a refresh.

    Args:
        devices (List[EcoflowDevice]): List of devices to scan for expired cache.
    """
    for device in devices:
      if self._need_update_cached_power(device):
        await self._update_cached_power(device)
        break
