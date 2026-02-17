import json
import requests

from deye_utils import DeyeUtils
from deye_registers_base_cache_manager import DeyeRegistersBaseCacheManager

# ---------------------------------------------------------------
# Class for caching register data remotely on JSON caching server
# ---------------------------------------------------------------
class DeyeRegistersRemoteCacheManager(DeyeRegistersBaseCacheManager):
  def __init__(
    self,
    name: str,
    cache_server_endpoint: str,
    verbose = False,
  ):
    super().__init__(name, verbose)
    self._cache_server_endpoint = cache_server_endpoint
    # Added inverter name to the endpoint path to match FastAPI routes
    self._inverter_cache_endpoint = f"{cache_server_endpoint}/{name}"
    # Create a persistent session for connection pooling
    self._session = requests.Session()

    if self.verbose:
      print(f"{self.name} {self.__class__.__name__} initialized")

  def _get_json(self) -> str:
    """
    Used for general data retrieval.
    Fetches the current state of the cache to be used for reading and displaying data.
    """
    try:
      # Reusing the connection via self._session
      response = self._session.get(self._inverter_cache_endpoint, timeout = 5)
      response.raise_for_status()

      # FastAPI returns a dict, we convert it back to string to satisfy base class
      return response.text
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self.name}: error reading "
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
        e, f"{self.name}: error writing remote cache "
        f"to {self._inverter_cache_endpoint}") from e

  def _reset(self) -> None:
    try:
      # Clear all cached data for all inverters
      response = requests.delete(self._inverter_cache_endpoint, timeout = 5)

      # Check if the status code is 2xx
      response.raise_for_status()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self.name}: error writing remote cache "
        f"to {self._inverter_cache_endpoint}") from e

  def close(self):
    """Properly close the session when done."""
    self._session.close()
