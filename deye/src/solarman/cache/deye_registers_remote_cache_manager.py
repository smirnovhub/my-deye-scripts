from http import HTTPStatus
from urllib.parse import urljoin

from deye_utils import DeyeUtils
from deye_exceptions import DeyeCacheException
from http_session_singleton import HttpSessionSingleton
from deye_registers_base_cache_manager import DeyeRegistersBaseCacheManager
from deye_register_cache_hit_rate import DeyeRegisterCacheHitRate

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
    self._average_hit_rate_endpoint = urljoin(remote_cache_server, f"/average/{self._name}-{self._serial}")

    self._session = HttpSessionSingleton().session

    self._logger.info(f"{self._name} {self.__class__.__name__} initialized")
    self._logger.info(f"{self._name} remote cache endpoint: {self._inverter_cache_endpoint}")

  def _get_json(self) -> str:
    """
    Used for general data retrieval.
    Fetches the current state of the cache to be used for reading and displaying data.
    """
    try:
      with self._session.get(self._inverter_cache_endpoint, timeout = 5) as response:
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
      headers = {'Content-Type': 'application/json'}

      with self._session.post(
          self._inverter_cache_endpoint,
          data = json_string,
          headers = headers,
          timeout = 5,
      ) as response:
        response.raise_for_status()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error writing remote cache "
        f"to {self._inverter_cache_endpoint}") from e

  def _reset(self) -> None:
    try:
      # Clear all cached data for all inverters
      with self._session.delete(self._inverter_cache_endpoint, timeout = 5) as response:
        # Check if the status code is 2xx
        if response.status_code != HTTPStatus.NOT_FOUND:
          response.raise_for_status()
    except Exception as e:
      raise DeyeUtils.get_reraised_exception(
        e, f"{self._name}: error resetting remote cache "
        f"for {self._inverter_cache_endpoint}") from e

  def is_cache_available(self) -> bool:
    """
    Check if the remote cache server is available by sending a ping request.

    Returns:
      bool: True if cache is available for use

    Raises:
      DeyeCacheException: If the cache is not available.
    """
    try:
      ping_endpoint = urljoin(self._remote_cache_server, "/ping")
      with self._session.get(ping_endpoint, timeout = 3) as response:
        response.raise_for_status()
      return True
    except Exception as e:
      raise DeyeCacheException(f"{self._name}: remote cache server "
                               f"{self._remote_cache_server} seems to be down") from e

  def get_cache_hit_rate(self) -> DeyeRegisterCacheHitRate:
    try:
      with self._session.get(self._average_hit_rate_endpoint, timeout = 3) as response:
        if response.status_code == HTTPStatus.NOT_FOUND:
          self._logger.warning(f'{self._name} global cache hit rate not found')
          return DeyeRegisterCacheHitRate.zero()
        response.raise_for_status()
        js = response.json()

      rate = DeyeRegisterCacheHitRate(
        got_from_cache_count = js.get("count1", 0),
        got_from_inverter_count = js.get("count2", 0),
        total_count = js.get("total", 0),
        cache_hit_rate = js.get("average", 0.0),
      )

      self._logger.info(
        "%s global cache hit rate: %g%% %g/%g",
        self._name,
        rate.cache_hit_rate_percent,
        rate.got_from_cache_count,
        rate.total_count,
      )

      return rate
    except Exception as e:
      self._logger.error("%s: error getting global cache hit rate: %s", self._name, e, exc_info = True)
      raise

  def update_cache_hit_rate(
    self,
    got_from_cache: int,
    got_from_inverter: int,
  ) -> DeyeRegisterCacheHitRate:
    try:
      request = f"{got_from_cache}/{got_from_inverter}" # count1/count2
      url = urljoin(f"{self._average_hit_rate_endpoint}/", request)

      with self._session.post(url, timeout = 3) as response:
        response.raise_for_status()
        js = response.json()

      rate = DeyeRegisterCacheHitRate(
        got_from_cache_count = js.get("count1", 0),
        got_from_inverter_count = js.get("count2", 0),
        total_count = js.get("total", 0),
        cache_hit_rate = js.get("average", 0.0),
      )

      self._logger.info(
        "%s global cache hit rate: %g%% %g/%g",
        self._name,
        rate.cache_hit_rate_percent,
        rate.got_from_cache_count,
        rate.total_count,
      )

      return rate
    except Exception as e:
      self._logger.error("%s: error updating global cache hit rate: %s", self._name, e, exc_info = True)
      raise

  def reset_cache_hit_rate(self) -> None:
    try:
      with self._session.delete(self._average_hit_rate_endpoint, timeout = 3) as response:
        if response.status_code == HTTPStatus.NOT_FOUND:
          self._logger.warning(f'{self._name} global cache hit rate not found')
        else:
          response.raise_for_status()
          self._logger.info(f'{self._name} global cache hit rate reset successful')
    except Exception as e:
      self._logger.error("%s: error resetting global cache hit rate: %s", self._name, e, exc_info = True)
