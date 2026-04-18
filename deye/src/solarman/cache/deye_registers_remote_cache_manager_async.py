from http import HTTPStatus
from urllib.parse import urljoin

from deye_utils import DeyeUtils
from deye_exceptions import DeyeCacheException
from deye_registers_base_cache_manager_async import DeyeRegistersBaseCacheManagerAsync
from http_session_singleton_async import HttpSessionSingletonAsync

# ---------------------------------------------------------------
# Class for caching register data remotely on JSON caching server
# ---------------------------------------------------------------
class DeyeRegistersRemoteCacheManagerAsync(DeyeRegistersBaseCacheManagerAsync):
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
    self._average_hit_rate_endpoint = urljoin(remote_cache_server, f"/average/{self._name}-{self._serial}")

    self._logger.info(f"{self._name} {self.__class__.__name__} initialized")
    self._logger.info(f"{self._name} remote cache endpoint: {self._inverter_cache_endpoint}")

  async def _get_json(self) -> str:
    """
    Used for general data retrieval.
    Fetches the current state of the cache to be used for reading and displaying data.
    """
    try:
      session = await HttpSessionSingletonAsync.get_session()
      async with session.get(self._inverter_cache_endpoint) as response:
        # Treat 404 as an empty result (key is missing in the cache)
        if response.status == HTTPStatus.NOT_FOUND:
          return "{}"

        response.raise_for_status()

        # FastAPI returns a dict, we convert it back to string to satisfy base class
        return await response.text()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error reading "
        f"remote cache from {self._inverter_cache_endpoint}") from e

  async def _read_json(self) -> str:
    """
    Returns an empty string because remote server performs data merging 
    on its side via dict.update(). Local read-modify-write cycle is 
    not required for the remote cache manager.
    """
    return ''

  async def _save_json(self, json_string: str) -> None:
    """Send JSON data to the remote server using persistent session."""
    try:
      headers = {'Content-Type': 'application/json'}
      session = await HttpSessionSingletonAsync.get_session()

      async with session.post(self._inverter_cache_endpoint, data = json_string, headers = headers) as response:
        response.raise_for_status()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error writing remote cache "
        f"to {self._inverter_cache_endpoint}") from e

  async def _reset(self) -> None:
    try:
      # Clear all cached data for all inverters
      session = await HttpSessionSingletonAsync.get_session()
      async with session.delete(self._inverter_cache_endpoint) as response:
        # Check if the status code is 2xx
        if response.status != HTTPStatus.NOT_FOUND:
          response.raise_for_status()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error resetting remote cache "
        f"for {self._inverter_cache_endpoint}") from e

  async def _is_cache_available(self) -> bool:
    """
    Check if the remote cache server is available by sending a ping request.

    Returns:
      bool: True if cache is available for use

    Raises:
      DeyeCacheException: If the cache is not available.
    """
    try:
      ping_endpoint = urljoin(self._remote_cache_server, "/ping")

      session = await HttpSessionSingletonAsync.get_session()
      async with session.get(ping_endpoint) as response:
        response.raise_for_status()
      return True
    except Exception as e:
      raise DeyeCacheException(f"{self._name}: remote cache server "
                               f"{self._remote_cache_server} seems to be down") from e

  async def update_cache_hit_rate(
    self,
    got_from_cache: int,
    got_from_inverter: int,
  ) -> None:
    try:
      session = await HttpSessionSingletonAsync.get_session()
      request = f"{got_from_cache}/{got_from_inverter}"
      url = urljoin(f"{self._average_hit_rate_endpoint}/", request)

      async with session.post(url) as response:
        response.raise_for_status()
        js = await response.json()

      hit_rate = round(js.get("average", 0.0) * 100)
      cache_cnt = js.get("total1", 0)
      total = js.get("total1", 0) + js.get("total2", 0)

      self._logger.info(f'{self._name} global cache hit rate: {hit_rate}% {cache_cnt:g}/{total:g}')
    except Exception as e:
      self._logger.error("%s: error updating global cache hit rate: %s", self._name, e, exc_info = True)

  async def reset_cache_hit_rate(self) -> None:
    try:
      session = await HttpSessionSingletonAsync.get_session()
      async with session.delete(self._average_hit_rate_endpoint) as response:
        if response.status == HTTPStatus.NOT_FOUND:
          self._logger.warning(f'{self._name} global cache hit rate not found')
        else:
          response.raise_for_status()
          self._logger.info(f'{self._name} global cache hit rate reset successful')
    except Exception as e:
      self._logger.error("%s: error resetting global cache hit rate: %s", self._name, e, exc_info = True)
