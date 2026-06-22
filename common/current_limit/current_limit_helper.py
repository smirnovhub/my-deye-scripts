from datetime import date
from urllib.parse import urljoin

from env_utils import EnvUtils
from current_limit_config_dto import CurrentLimitConfigDto
from current_limit_settings_dto import CurrentLimitSettingsDto
from http_session_singleton_async import HttpSessionSingletonAsync

class CurrentLimitHelper:
  CURRENT_LIMIT_CONFIG_URL = '/storage/current-limit-config'
  CURRENT_LIMIT_SETTINGS_URL = '/storage/current-limit-settings'

  @staticmethod
  async def load_config() -> CurrentLimitConfigDto:
    server_url = EnvUtils.get_remote_cache_server_url()
    url = urljoin(server_url, CurrentLimitHelper.CURRENT_LIMIT_CONFIG_URL)
    session = await HttpSessionSingletonAsync.get_session()

    async with session.get(url) as response:
      response.raise_for_status()
      payload = await response.text()
      config = CurrentLimitConfigDto.from_json(payload)

      today = date.today()
      config.dont_regulate_dates = [d for d in config.dont_regulate_dates if d >= today]

      return config

  @staticmethod
  async def save_config(config: CurrentLimitConfigDto) -> None:
    today = date.today()
    config.dont_regulate_dates = [d for d in config.dont_regulate_dates if d >= today]

    server_url = EnvUtils.get_remote_cache_server_url()
    url = urljoin(server_url, CurrentLimitHelper.CURRENT_LIMIT_CONFIG_URL)
    session = await HttpSessionSingletonAsync.get_session()

    async with session.post(url, json = config.to_dict()) as response:
      response.raise_for_status()

  @staticmethod
  async def load_settings() -> CurrentLimitSettingsDto:
    server_url = EnvUtils.get_remote_cache_server_url()
    url = urljoin(server_url, CurrentLimitHelper.CURRENT_LIMIT_SETTINGS_URL)
    session = await HttpSessionSingletonAsync.get_session()

    async with session.get(url) as response:
      response.raise_for_status()
      payload = await response.text()
      return CurrentLimitSettingsDto.from_json(payload)

  @staticmethod
  async def save_settings(settings: CurrentLimitSettingsDto) -> None:
    server_url = EnvUtils.get_remote_cache_server_url()
    url = urljoin(server_url, CurrentLimitHelper.CURRENT_LIMIT_SETTINGS_URL)
    session = await HttpSessionSingletonAsync.get_session()

    async with session.post(url, json = settings.to_dict()) as response:
      response.raise_for_status()

  @staticmethod
  async def check_storage_server_available() -> None:
    server_url = EnvUtils.get_remote_cache_server_url()
    url = urljoin(server_url, "/ping")
    session = await HttpSessionSingletonAsync.get_session()
    async with session.get(url, timeout = 3) as response:
      response.raise_for_status()
