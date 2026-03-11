import json

from http import HTTPStatus
from urllib.parse import urljoin

from deye_utils import DeyeUtils
from deye_exceptions import DeyeCacheException
from http_session_singleton import HttpSessionSingleton
from deye_registers_base_cache_manager import DeyeRegistersBaseCacheManager

# ---------------------------------------------------------------
# Class for caching register data remotely on JSON caching server
# ---------------------------------------------------------------
class DeyeRegistersRemoteCacheManager(DeyeRegistersBaseCacheManager):
  def __init__(
    self,
    name: str,
    serial: int,
    remote_cache_server: str,
  ):
    super().__init__(
      name = name,
      serial = serial,
    )

    self._remote_cache_server = remote_cache_server
    # Added inverter name to the endpoint path to match FastAPI routes
    self._inverter_cache_endpoint = urljoin(remote_cache_server, f"/cache/{self._name}-{self._serial}")
    self._session = HttpSessionSingleton().session

    self._logger.info(f"{self._name} {self.__class__.__name__} initialized")
    self._logger.info(f"{self._name} remote cache endpoint: {self._inverter_cache_endpoint}")

  def _get_json(self) -> str:
    """
    Used for general data retrieval.
    Fetches the current state of the cache to be used for reading and displaying data.
    """
    try:
      response = self._session.get(self._inverter_cache_endpoint, timeout = 5)

      # Treat 404 as an empty result (key is missing in the cache)
      if response.status_code == HTTPStatus.NOT_FOUND:
        return "{}"

      response.raise_for_status()

      # FastAPI returns a dict, we convert it back to string to satisfy base class
      return response.text
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error reading "
        f"remote cache from {self._inverter_cache_endpoint}") from e

  def _read_json(self) -> str:
    """
    Returns an empty string because remote server performs data merging 
    on its side via dict.update(). Local read-modify-write cycle is 
    not required for the remote cache manager.
    """
    return ''

  def _save_json(self, json_string: str) -> None:
    """Send JSON data to the remote server using persistent session."""
    try:
      # Parse input string to dict.
      # Note: json_string should follow the structure:
      # {"inverter": "...", "registers": {"150": {"time": ..., "data": [...]}}}
      data = json.loads(json_string)

      # Send as JSON. requests will automatically set Content-Type: application/json
      response = self._session.post(self._inverter_cache_endpoint, json = data, timeout = 5)
      response.raise_for_status()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error writing remote cache "
        f"to {self._inverter_cache_endpoint}") from e

  def _reset(self) -> None:
    try:
      # Clear all cached data for all inverters
      response = self._session.delete(self._inverter_cache_endpoint, timeout = 5)

      # Check if the status code is 2xx
      if response.status_code != HTTPStatus.NOT_FOUND:
        response.raise_for_status()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error resetting remote cache "
        f"for {self._inverter_cache_endpoint}") from e

  def _is_cache_available(self) -> bool:
    """
    Check if the remote cache server is available by sending a ping request.

    Returns:
      bool: True if cache is available for use

    Raises:
      DeyeCacheException: If the cache is not available.
    """
    try:
      ping_endpoint = urljoin(self._remote_cache_server, "/ping")
      response = self._session.get(ping_endpoint, timeout = 3)
      response.raise_for_status()
      return True
    except Exception as e:
      raise DeyeCacheException(f"{self._name}: remote cache server "
                               f"{self._remote_cache_server} seems to be down") from e
