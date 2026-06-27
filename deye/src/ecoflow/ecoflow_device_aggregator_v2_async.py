import random
import logging

from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ecoflow_device import EcoflowDevice
from ecoflow_devices import EcoflowDevices
from ecoflow_powerstream_interactor_async import EcoflowPowerStreamInteractorAsync

class EcoflowDeviceAggregatorV2Async:
  """
  An asynchronous aggregator designed to orchestrate and optimize power distribution 
  across multiple EcoFlow devices simultaneously.

  Optimization Strategy:
    1. API Rate-Limit Protection: Minimizes outgoing requests to the EcoFlow API by utilizing 
       a dynamic, localized power cache with a staggered 10-minute refresh interval.
    2. Request Anti-Collision (Jitter): Applies a randomized jitter to update intervals, 
       preventing multiple devices from expiring simultaneously and flooding the network.
    3. Single-Device Polling: Limits cache synchronization to a maximum of one expired 
       device per total power computation cycle, flattening API traffic spikes.
    4. Balanced Power Staircase: Distributes incoming load adjustments incrementally using a 
       configurable threshold constraint. Devices with close power parameters are toggled 
       randomly, avoiding localized hardware wear and balancing overall execution.

  Parameters:
    access_key (str): Ecoflow API access key.
    secret_key (str): Ecoflow API secret key.
    equal_power_threshold_watt (int): The power deadband threshold in watts. When the power 
        difference between devices is less than or equal to this value, the aggregator considers 
        them equal and selects a device at random to balance the load evenly.
    **kwargs: Optional keyword arguments passed to EcoflowPowerStreamInteractor:
      - name (str): Name identifier for logging (default: 'ecoflow').
      - verbose (bool): Enable verbose logging (default: False).
  """
  def __init__(
    self,
    access_key: str,
    secret_key: str,
    equal_power_threshold_watt: int,
    delay_between_requests: Optional[timedelta] = None,
    **kwargs,
  ):
    self._devices = EcoflowDevices()
    self._interactor = EcoflowPowerStreamInteractorAsync(
      access_key = access_key,
      secret_key = secret_key,
      delay_between_requests = delay_between_requests,
      **kwargs,
    )

    self._name = kwargs.get('name', 'ecoflow')
    self._verbose = kwargs.get('verbose', False)
    self._power_cache: Dict[EcoflowDevice, int] = {}
    self._power_cache_last_update: Dict[EcoflowDevice, datetime] = {}
    self._power_cache_update_interval = timedelta(minutes = 10)
    self._power_cache_update_interval_deviation = timedelta(minutes = 5)
    self._equal_power_threshold_watt = equal_power_threshold_watt
    self._online_devices: List[EcoflowDevice] = []
    self._online_devices_last_update: datetime = datetime.min
    self._online_devices_update_interval = timedelta(minutes = 5)
    self._logger = logging.getLogger()

  async def get_online_devices_count(self) -> int:
    if self._need_update_online_devices():
      await self._update_online_devices()
    return len(self._online_devices)

  @property
  def max_power(self) -> int:
    """
    Calculate the sum of the maximum configurable power of all devices.

    Returns:
      int: Sum of max_power across all devices.
    """
    return sum(device.max_power for device in self._online_devices)

  @property
  def max_real_power(self) -> int:
    """
    Calculate the sum of the maximum real output power of all devices.

    Returns:
      int: Sum of max_real_power across all devices.
    """
    return sum(device.max_real_power for device in self._online_devices)

  async def _try_set_power(self, device: EcoflowDevice, power: int) -> None:
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
    if device not in self._online_devices:
      self._logger.error(f"{self._name}: failed to set power for {device.name} ({device.serial}): "
                         "device is offline")
      return

    power = int(round(max(0, min(power, device.max_power))))

    if self._verbose:
      self._logger.info(f'{self._name}: setting power {power} W for {device.name}...')

    old_power = self.get_cached_power(device)

    if self._verbose:
      self._logger.info(f'{self._name}: got power {old_power} W from cache for {device.name}')

    if old_power == power:
      if self._verbose:
        self._logger.info(f'{self._name}: new power ({power} W) for {device.name} is the same as old power. do nothing')
      return

    if self._verbose:
      self._logger.info(f'{self._name}: changing power for {device.name} to {power} W...')

    try:
      await self._interactor.set_power(device, power)
    except Exception as e:
      self._logger.error(f"{self._name}: failed to set power for {device.name} ({device.serial}): {e}")
      return

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
    if self._need_update_online_devices():
      await self._update_online_devices()

    if not self._online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for get_cached_total_power()')
      return 0

    await self._update_cached_power_for_one_device_at_once(self._online_devices)

    total_power = 0
    for device in self._online_devices:
      power = self.get_cached_power(device)
      if power > 0:
        total_power += power

    return total_power

  def _get_device_with_min_power(
    self,
    devices: List[EcoflowDevice],
    threshold: int = 0,
  ) -> EcoflowDevice:
    """
    Find an online device with the lowest cached power.
    
    Groups all devices whose cached power is within the specified threshold 
    from the absolute minimum power, and selects one from them at random.
    This prevents the same device from being selected repeatedly when power 
    values are close.

    Args:
        devices (List[EcoflowDevice]): A list of currently online EcoFlow devices.

    Returns:
        EcoflowDevice: The selected device to increase power on.
    """
    # Track devices and their corresponding cached power values
    device_powers: Dict[EcoflowDevice, int] = {}
    for dev in devices:
      device_powers[dev] = self.get_cached_power(dev)

    # Find the minimum power value among all devices
    min_power = min(device_powers.values())

    # Collect all devices that are close to the minimum within the threshold
    candidates = [d for d in devices if device_powers[d] - min_power <= threshold]

    # Select a random device from the candidates
    return random.choice(candidates)

  def _get_device_with_max_power(
    self,
    devices: List[EcoflowDevice],
    threshold: int = 0,
  ) -> EcoflowDevice:
    """
    Find an online device with the highest cached power.
    
    Groups all devices whose cached power is within the specified threshold 
    from the absolute maximum power, and selects one from them at random.
    This prevents the same device from being selected repeatedly when power 
    values are close.

    Args:
        devices (List[EcoflowDevice]): A list of currently online EcoFlow devices.

    Returns:
        EcoflowDevice: The selected device to decrease power on.
    """
    # Track devices and their corresponding cached power values
    device_powers: Dict[EcoflowDevice, int] = {}
    for dev in devices:
      device_powers[dev] = self.get_cached_power(dev)

    # Find the maximum power value among all devices
    max_power = max(device_powers.values())

    # Collect all devices that are close to the maximum within the threshold
    candidates = [d for d in devices if max_power - device_powers[d] <= threshold]

    # Select a random device from the candidates
    return random.choice(candidates)

  def _get_power_disbalance(self, devices: List[EcoflowDevice]) -> int:
    """
    Calculate the difference between the maximum and minimum cached power 
    among the provided list of online devices.

    Args:
        devices (List[EcoflowDevice]): The list of devices to check.
    Returns:
        int: The power disbalance in watts. Returns 0 if there are fewer 
              than two active devices.
    """
    # Extract cached power values using the device identification
    powers = [self.get_cached_power(device) for device in devices]

    # Calculate the absolute difference between the highest and lowest values
    disbalance = max(powers) - min(powers)

    self._logger.info(f'{self._name}: power disbalance between devices is {disbalance} W')
    return disbalance

  async def change_power(self, power_delta: int) -> None:
    """
    Args:
      power_delta (int): Total change in power in watts. Can be positive
                 (increase) or negative (decrease).
    """
    if abs(power_delta) < 5:
      self._logger.warning(f'{self._name}: power delta is too low in change_power()')
      return

    if self._need_update_online_devices():
      await self._update_online_devices()

    if not self._online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for change_power()')
      return

    if power_delta > 0:
      device = self._get_device_with_min_power(
        devices = self._online_devices,
        threshold = self._equal_power_threshold_watt,
      )
    else:
      device = self._get_device_with_max_power(
        devices = self._online_devices,
        threshold = self._equal_power_threshold_watt,
      )

    if self._need_update_cached_power(device):
      await self._update_cached_power(device)

    power = self.get_cached_power(device)
    await self._try_set_power(device, power + power_delta)

  async def equalize_power(self, power_delta: int) -> None:
    if abs(power_delta) < 5:
      self._logger.warning(f'{self._name}: power delta is too low in equalize_power()')
      return

    if self._need_update_online_devices():
      await self._update_online_devices()

    if not self._online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for equalize_power()')
      return

    disbalance = self._get_power_disbalance(self._online_devices)
    if disbalance <= 0:
      self._logger.info(f'{self._name}: power for all devices is equal')
      return

    delta = min(abs(power_delta), disbalance)
    sign = random.choice([-1, 1])

    if sign > 0:
      device = self._get_device_with_min_power(self._online_devices)
    else:
      device = self._get_device_with_max_power(self._online_devices)

    if self._need_update_cached_power(device):
      await self._update_cached_power(device)

    power = self.get_cached_power(device)
    await self._try_set_power(device, power + delta * sign)

  async def set_max_power(self) -> None:
    """
    Set each online device to its maximum configurable power.

    Offline devices have their cached power reset to prevent stale values.
    """
    if self._need_update_online_devices():
      await self._update_online_devices()

    if not self._online_devices:
      if self._verbose:
        self._logger.info(f'{self._name}: no online devices for set_max_power()')
      return

    device = self._get_device_with_min_power(
      devices = self._online_devices,
      threshold = self._equal_power_threshold_watt,
    )

    if self._need_update_cached_power(device):
      await self._update_cached_power(device)

    await self._try_set_power(device, device.max_power)

  def get_cached_power(self, device: EcoflowDevice) -> int:
    return self._power_cache.get(device, -1)

  def _set_cached_power(self, device: EcoflowDevice, power: int) -> None:
    self._power_cache[device] = power
    self._power_cache_last_update[device] = datetime.now()
    self._logger.info(f"{self._name}: cached power last update time for {device.name} has been updated.")

  def _need_update_cached_power(self, device: EcoflowDevice) -> bool:
    last_update = self._power_cache_last_update.get(device, datetime.min)
    jitter = self._get_random_jitter(self._power_cache_update_interval_deviation)
    update_interval = self._power_cache_update_interval + jitter
    return datetime.now() - last_update > update_interval

  async def _update_cached_power(self, device: EcoflowDevice) -> None:
    power = await self._interactor.get_power(device)
    self._power_cache[device] = power

    jitter = timedelta()
    if device not in self._power_cache_last_update:
      # Use update interval as initial deviation
      jitter = self._get_random_jitter(self._power_cache_update_interval)

    self._power_cache_last_update[device] = datetime.now() + jitter
    self._logger.info(f"{self._name}: cached power for {device.name} has been updated to {power} W.")

  async def _update_cached_power_for_one_device_at_once(self, devices: List[EcoflowDevice]) -> None:
    """
    Find and update the cache via API for strictly the first device that requires a refresh.

    Args:
        devices (List[EcoflowDevice]): List of devices to scan for expired cache.
    """
    shuffled_devices = list(devices)
    random.shuffle(shuffled_devices)

    for device in shuffled_devices:
      if self._need_update_cached_power(device):
        await self._update_cached_power(device)
        break

  def _get_random_jitter(self, deviation: timedelta) -> timedelta:
    deviation_seconds = int(deviation.total_seconds())
    return timedelta(seconds = random.randint(0, deviation_seconds))

  def _need_update_online_devices(self) -> bool:
    return datetime.now() - self._online_devices_last_update > self._online_devices_update_interval

  async def _update_online_devices(self) -> None:
    previously_online = {d for d in self._online_devices}

    self._online_devices = await self._interactor.get_online_devices(self._devices)
    self._online_devices_last_update = datetime.now()
    self._logger.info(f"{self._name}: online devices updated: {len(self._online_devices)} devices are online")

    for device in self._online_devices:
      if device not in previously_online:
        self._power_cache.pop(device, None)
        self._power_cache_last_update.pop(device, None)
        self._logger.info(f"{self._name}: device {device.name} came online, power cache cleared")
