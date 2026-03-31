import requests
import logging

from typing import Any, Dict, List, Optional
from http import HTTPStatus

from ecoflow_utils import EcoflowUtils
from ecoflow_device import EcoflowDevice
from ecoflow_devices import EcoflowDevices
from ecoflow_device_status import EcoflowDeviceStatus
from http_session_singleton import HttpSessionSingleton

from ecoflow_exceptions import (
  EcoflowHttpErrorException,
  EcoflowResponseErrorException,
)

class EcoflowPowerStreamInteractor:
  """
  Interacts with Ecoflow devices over the Ecoflow cloud API.

  Provides methods to:
  - Retrieve online device list
  - Get device power usage
  - Set device power limits
  - Handle API errors

  Parameters:
    access_key (str): Ecoflow API access key.
    secret_key (str): Ecoflow API secret key.
    **kwargs: Optional keyword arguments:
      - name (str): Name identifier for logging (default: 'ecoflow').
      - verbose (bool): Enable verbose logging (default: False).
  """
  def __init__(
    self,
    access_key: str,
    secret_key: str,
    **kwargs,
  ):
    self._access_key = access_key
    self._secret_key = secret_key
    self._name = kwargs.get('name', 'ecoflow')
    self._verbose = kwargs.get('verbose', False)
    self._quota_url = 'https://api.ecoflow.com/iot-open/sign/device/quota'
    self._device_url = 'https://api.ecoflow.com/iot-open/sign/device/list'
    self._set_permanent_watts_cmd = 'WN511_SET_PERMANENT_WATTS_PACK'
    self._permanent_watts_field = '20_1.permanentWatts'
    self._power_scale = 10
    self._session = HttpSessionSingleton().session
    self._logger = logging.getLogger()
    self._logger.setLevel(logging.INFO)

  def get_device_status(self, device: EcoflowDevice, payload: Dict[str, Any]) -> EcoflowDeviceStatus:
    """
    Get the online status of a specific device from API payload.

    Parameters:
      device (EcoflowDevice): Device instance to check.
      payload (Dict[str, Any]): JSON payload from the device list API.

    Returns:
      EcoflowDeviceStatus: Status of the device (online, offline, unknown, etc.).
    """
    for status in payload.get('data', []):
      if status.get('sn') == device.serial and status.get('productName') == device.device_type:
        online_status = status.get('online', 0)
        for state in EcoflowDeviceStatus:
          if online_status == state.value:
            return state
        return EcoflowDeviceStatus.unknown

    return EcoflowDeviceStatus.unknown

  def get_online_devices(self, devices: EcoflowDevices) -> List[EcoflowDevice]:
    """
    Return a list of devices that are currently online.

    Parameters:
      devices (EcoflowDevices): Collection of devices to check.

    Raises:
      EcoflowException: If API call fails or returns an error.

    Returns:
      List[EcoflowDevice]: Devices that are online according to the API.
    """
    if self._verbose:
      self._logger.info(f'{self._name}: getting devices list...')

    with self._get_request(
        self._device_url,
        self._access_key,
        self._secret_key,
    ) as response:
      if response.status_code != HTTPStatus.OK:
        if self._verbose:
          self._logger.info(
            f'{self._name}: server returned http error {response.status_code} while getting devices list')
        raise EcoflowHttpErrorException(
          f'{self._name}: server returned http error {response.status_code} while getting devices list')

      js = response.json()

    self._check_error(js, 'getting devices list')

    if self._verbose:
      self._logger.info(f'{self._name}: get_online_devices() result {js}')

    online_devices = []

    for device in devices.devices:
      device_status = self.get_device_status(device, js)
      if device_status == EcoflowDeviceStatus.online:
        if self._verbose:
          self._logger.info(f'{self._name}: device {device.name} status is {device_status.name}')
        online_devices.append(device)

    return online_devices

  def get_power(self, device: EcoflowDevice) -> int:
    """
    Retrieve the current permanent power setting of a device.

    Parameters:
      device (EcoflowDevice): Device to query.

    Raises:
      EcoflowException: If API call fails or returns an error.

    Returns:
      int: Current power in watts (rounded from API value).
    """
    quotas = [self._permanent_watts_field]
    params = {'quotas': quotas}

    if self._verbose:
      self._logger.info(f'{self._name}: getting power for {device.name}...')

    with self._post_request(
        self._quota_url,
        self._access_key,
        self._secret_key,
      {
        'sn': device.serial,
        'params': params
      },
    ) as response:
      if response.status_code != HTTPStatus.OK:
        if self._verbose:
          self._logger.info(
            f'{self._name}: server returned http error {response.status_code} while getting power for {device.name}')
        raise EcoflowHttpErrorException(
          f'{self._name}: server returned http error {response.status_code} while getting power for {device.name}')

      js = response.json()

    self._check_error(js, device.name)

    if self._verbose:
      self._logger.info(f'{self._name}: get_power() result {js}')

    power = int(round(js['data'][self._permanent_watts_field] / self._power_scale))

    if self._verbose:
      self._logger.info(f'{self._name}: current power for {device.name} is {power} W')

    return power

  def set_power(self, device: EcoflowDevice, power: int):
    """
    Set a new permanent power limit for a device.

    Parameters:
      device (EcoflowDevice): Device to configure.
      power (int): Power value in watts to set (clamped to device limits).

    Raises:
      EcoflowException: If API call fails or returns an error.
    """
    power = max(0, min(power, device.max_power))

    if self._verbose:
      self._logger.info(f'{self._name}: set new power for {device.name} to {power} W')

    params = {'permanentWatts': power * self._power_scale}

    with self._put_request(
        self._quota_url,
        self._access_key,
        self._secret_key,
      {
        'sn': device.serial,
        'cmdCode': self._set_permanent_watts_cmd,
        'params': params
      },
    ) as response:
      if response.status_code != HTTPStatus.OK:
        if self._verbose:
          self._logger.info(
            f'{self._name}: server returned http error {response.status_code} while setting power for {device.name}')
        raise EcoflowHttpErrorException(
          f'{self._name}: server returned http error {response.status_code} while setting power for {device.name}')

      js = response.json()

    self._check_error(js, device.name)

    if self._verbose:
      self._logger.info(f'{self._name}: set_power() result {js}')

  def _check_error(self, js: Dict[str, Any], device_name: str):
    """
    Validate API response for errors and raise exception if needed.

    Parameters:
      js (Dict[str, Any]): JSON response from Ecoflow API.
      device_name (str): Name of the device related to this response.

    Raises:
      EcoflowException: If API response contains error code or invalid format.
    """
    if 'code' not in js:
      raise EcoflowResponseErrorException(f'{self._name}: response missing \'code\' field for {device_name}')

    try:
      code = int(js['code'])
    except Exception:
      raise EcoflowResponseErrorException(f'{self._name}: invalid \'code\' value ({js["code"]}) for {device_name}')

    if code != 0:
      message = f': {js["message"]}' if 'message' in js else ''
      raise EcoflowResponseErrorException(f'{self._name}: server returned error code {code} for {device_name}{message}')

  def _put_request(
    self,
    url: str,
    key: str,
    secret: str,
    params: Optional[Dict[str, Any]] = None,
  ) -> requests.Response:
    """
    Send an HTTP PUT request with signed headers and optional JSON body.

    Args:
        url (str): URL to send the request to.
        key (str): API access key.
        secret (str): API secret for signing.
        params (dict, optional): Optional JSON body to include. Defaults to None.

    Returns:
        requests.Response: Response object returned by the requests library.
    """
    headers = EcoflowUtils.get_headers(key, secret, params)
    return self._session.put(url, headers = headers, json = params, timeout = 10)

  def _get_request(
    self,
    url: str,
    key: str,
    secret: str,
    params: Optional[Dict[str, Any]] = None,
  ) -> requests.Response:
    """
    Send an HTTP GET request with signed headers and optional JSON body.

    Args:
        url (str): URL to send the request to.
        key (str): API access key.
        secret (str): API secret for signing.
        params (dict, optional): Optional JSON body to include. Defaults to None.

    Returns:
        requests.Response: Response object returned by the requests library.
    """
    headers = EcoflowUtils.get_headers(key, secret, params)
    return self._session.get(url, headers = headers, json = params, timeout = 10)

  def _post_request(
    self,
    url: str,
    key: str,
    secret: str,
    params: Optional[Dict[str, Any]] = None,
  ) -> requests.Response:
    """
    Send an HTTP POST request with signed headers and optional JSON body.

    Args:
        url (str): URL to send the request to.
        key (str): API access key.
        secret (str): API secret for signing.
        params (dict, optional): Optional JSON body to include. Defaults to None.

    Returns:
        requests.Response: Response object returned by the requests library.
    """
    headers = EcoflowUtils.get_headers(key, secret, params)
    return self._session.post(url, headers = headers, json = params, timeout = 10)
