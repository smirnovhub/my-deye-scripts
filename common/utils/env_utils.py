import os
import re

class EnvUtils:

  IS_TEST_RUN = "IS_TEST_RUN"

  DEYE_LOG_NAME = "DEYE_LOG_NAME"
  DEYE_MASTER_LOGGER_HOST = "DEYE_MASTER_LOGGER_HOST"
  DEYE_MASTER_LOGGER_SERIAL = "DEYE_MASTER_LOGGER_SERIAL"
  DEYE_MASTER_LOGGER_PORT = "DEYE_MASTER_LOGGER_PORT"
  DEYE_SLAVE_LOGGER_HOST = "DEYE_SLAVE{0}_LOGGER_HOST"
  DEYE_SLAVE_LOGGER_SERIAL = "DEYE_SLAVE{0}_LOGGER_SERIAL"
  DEYE_SLAVE_LOGGER_PORT = "DEYE_SLAVE{0}_LOGGER_PORT"
  DEYE_GPS_LATITUDE = "DEYE_GPS_LATITUDE"
  DEYE_GPS_LONGITUDE = "DEYE_GPS_LONGITUDE"
  DEYE_PV_ENERGY_COSTS_JSON = "DEYE_PV_ENERGY_COSTS_JSON"
  DEYE_GRID_PURCHASED_ENERGY_COSTS_JSON = "DEYE_GRID_PURCHASED_ENERGY_COSTS_JSON"
  DEYE_GRID_FEED_IN_ENERGY_COSTS_JSON = "DEYE_GRID_FEED_IN_ENERGY_COSTS_JSON"
  DEYE_GEN_ENERGY_COSTS_JSON = "DEYE_GEN_ENERGY_COSTS_JSON"
  DEYE_ENERGY_COST_CURRENCY_CODE = "DEYE_ENERGY_COST_CURRENCY_CODE"
  DEYE_WEB_REGISTER_VALUE_CORRECTIONS_JSON = "DEYE_WEB_REGISTER_VALUE_CORRECTIONS_JSON"
  DEYE_WEB_SECTION_TITLE_CORRECTIONS_JSON = "DEYE_WEB_SECTION_TITLE_CORRECTIONS_JSON"
  DEYE_WEB_REGISTER_DESCRIPTION_REPLACEMENTS_JSON = "DEYE_WEB_REGISTER_DESCRIPTION_REPLACEMENTS_JSON"
  DEYE_WEB_GRAPHS_BASE_URL = "DEYE_WEB_GRAPHS_BASE_URL"

  REMOTE_CACHE_SERVER_URL = "REMOTE_CACHE_SERVER_URL"
  REMOTE_GRAPH_SERVER_URL = "REMOTE_GRAPH_SERVER_URL"

  MIKROTIK_SERVER_URL = "MIKROTIK_SERVER_URL"
  SCHEDULER_SERVER_URL = "SCHEDULER_SERVER_URL"

  TELEGRAM_BOT_API_TOKEN = "TELEGRAM_BOT_API_TOKEN"
  TELEGRAM_BOT_API_TEST_TOKEN = "TELEGRAM_BOT_API_TEST_TOKEN"
  TELEGRAM_ADMIN_USER_ID = "TELEGRAM_ADMIN_USER_ID"
  TELEGRAM_PRIVATE_CHAT_ID = "TELEGRAM_PRIVATE_CHAT_ID"
  TELEGRAM_PUBLIC_CHAT_ID = "TELEGRAM_PUBLIC_CHAT_ID"

  OPEN_WEATHER_MAP_APPID = "OPEN_WEATHER_MAP_APPID"

  ECOFLOW_ACCESS_KEY = "ECOFLOW_ACCESS_KEY"
  ECOFLOW_SECRET_KEY = "ECOFLOW_SECRET_KEY"
  ECOFLOW_DEVICE_JSON = "ECOFLOW_DEVICE{0}_JSON"

  @staticmethod
  def get_master_logger_host() -> str:
    val = os.getenv(EnvUtils.DEYE_MASTER_LOGGER_HOST, '').strip()
    if not val:
      raise RuntimeError(f"Environment variable '{EnvUtils.DEYE_MASTER_LOGGER_HOST}' is not set")
    return val

  @staticmethod
  def get_master_logger_serial() -> int:
    return EnvUtils._get_logger_serial(EnvUtils.DEYE_MASTER_LOGGER_SERIAL)

  @staticmethod
  def get_master_logger_port() -> int:
    return EnvUtils._get_logger_port(EnvUtils.DEYE_MASTER_LOGGER_PORT)

  @staticmethod
  def get_slave_logger_host(num: int) -> str:
    return os.getenv(EnvUtils.DEYE_SLAVE_LOGGER_HOST.format(num), '').strip()

  @staticmethod
  def get_slave_logger_serial(num: int) -> int:
    return EnvUtils._get_logger_serial(EnvUtils.DEYE_SLAVE_LOGGER_SERIAL.format(num))

  @staticmethod
  def get_slave_logger_port(num: int) -> int:
    return EnvUtils._get_logger_port(EnvUtils.DEYE_SLAVE_LOGGER_PORT.format(num))

  @staticmethod
  def get_remote_cache_server_url() -> str:
    return os.getenv(EnvUtils.REMOTE_CACHE_SERVER_URL, '').strip()

  @staticmethod
  def get_remote_graph_server_url() -> str:
    return os.getenv(EnvUtils.REMOTE_GRAPH_SERVER_URL, '').strip()

  @staticmethod
  def get_mikrotik_server_url() -> str:
    return os.getenv(EnvUtils.MIKROTIK_SERVER_URL, '').strip()

  @staticmethod
  def get_scheduler_server_url() -> str:
    return os.getenv(EnvUtils.SCHEDULER_SERVER_URL, '').strip()

  @staticmethod
  def get_telegram_bot_api_token() -> str:
    val = os.getenv(EnvUtils.TELEGRAM_BOT_API_TOKEN, '').strip()
    if not val:
      raise RuntimeError(f"Environment variable '{EnvUtils.TELEGRAM_BOT_API_TOKEN}' is not set")

    if not re.fullmatch(r"^\d+:.+$", val):
      raise RuntimeError(f"Telegram bot API token '{EnvUtils.TELEGRAM_BOT_API_TOKEN}' is invalid")

    return val

  @staticmethod
  def get_telegram_admin_user_id() -> int:
    id = os.getenv(EnvUtils.TELEGRAM_ADMIN_USER_ID, '').strip()
    if not id:
      raise RuntimeError(f"Environment variable '{EnvUtils.TELEGRAM_ADMIN_USER_ID}' is not set")

    if not re.fullmatch(r"\d+", id):
      raise RuntimeError(f"Telegram admin user id '{EnvUtils.TELEGRAM_ADMIN_USER_ID}' is invalid")

    return int(id)

  @staticmethod
  def get_telegram_private_chat_id() -> str:
    val = os.getenv(EnvUtils.TELEGRAM_PRIVATE_CHAT_ID, '').strip()
    if not val:
      raise RuntimeError(f"Environment variable '{EnvUtils.TELEGRAM_PRIVATE_CHAT_ID}' is not set")

    if not re.fullmatch(r"\d+", val):
      raise RuntimeError(f"Telegram private chat id '{EnvUtils.TELEGRAM_PRIVATE_CHAT_ID}' is invalid")

    return val

  @staticmethod
  def get_telegram_public_chat_id() -> str:
    val = os.getenv(EnvUtils.TELEGRAM_PUBLIC_CHAT_ID, '').strip()

    if val and not re.fullmatch(r"-\d+", val):
      raise RuntimeError(f"Telegram public chat id '{EnvUtils.TELEGRAM_PUBLIC_CHAT_ID}' is invalid")

    return val

  @staticmethod
  def get_telegram_bot_api_test_token() -> str:
    val = os.getenv(EnvUtils.TELEGRAM_BOT_API_TEST_TOKEN, '').strip()
    if not val:
      raise RuntimeError(f"Environment variable '{EnvUtils.TELEGRAM_BOT_API_TEST_TOKEN}' is not set")

    if not re.fullmatch(r"^\d+:.+$", val):
      raise RuntimeError(f"Telegram bot API token '{EnvUtils.TELEGRAM_BOT_API_TEST_TOKEN}' is invalid")

    return val

  @staticmethod
  def get_gps_latitude() -> float:
    lat = os.getenv(EnvUtils.DEYE_GPS_LATITUDE, '50.45').strip()
    if not lat:
      raise RuntimeError(f"Environment variable '{EnvUtils.DEYE_GPS_LATITUDE}' is not set")

    try:
      val = float(lat)
      # Validate if latitude is within the legal range [-90, 90]
      if not (-90.0 <= val <= 90.0):
        raise ValueError(f"Latitude {val} is out of range [-90, 90]")
      return val
    except (ValueError, TypeError) as e:
      raise RuntimeError(f'Wrong GPS latitude format or value: {lat}') from e

  @staticmethod
  def get_gps_longitude() -> float:
    lon = os.getenv(EnvUtils.DEYE_GPS_LONGITUDE, '30.52').strip()
    if not lon:
      raise RuntimeError(f"Environment variable '{EnvUtils.DEYE_GPS_LONGITUDE}' is not set")

    try:
      val = float(lon)
      # Validate if longitude is within the legal range [-180, 180]
      if not (-180.0 <= val <= 180.0):
        raise ValueError(f"Longitude {val} is out of range [-180, 180]")
      return val
    except (ValueError, TypeError) as e:
      # Re-raise as RuntimeError with a descriptive message
      raise RuntimeError(f'Wrong GPS longitude format or value: {lon}') from e

  @staticmethod
  def get_open_weather_map_appid() -> str:
    return os.getenv(EnvUtils.OPEN_WEATHER_MAP_APPID, '').strip()

  @staticmethod
  def get_ecoflow_access_key() -> str:
    return os.getenv(EnvUtils.ECOFLOW_ACCESS_KEY, '').strip()

  @staticmethod
  def get_ecoflow_secret_key() -> str:
    return os.getenv(EnvUtils.ECOFLOW_SECRET_KEY, '').strip()

  @staticmethod
  def get_ecoflow_device_json(num: int) -> str:
    val = os.getenv(EnvUtils.ECOFLOW_DEVICE_JSON.format(num), '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_pv_energy_costs_json() -> str:
    val = os.getenv(EnvUtils.DEYE_PV_ENERGY_COSTS_JSON, '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_grid_purchased_energy_costs_json() -> str:
    val = os.getenv(EnvUtils.DEYE_GRID_PURCHASED_ENERGY_COSTS_JSON, '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_grid_feed_in_energy_costs_json() -> str:
    val = os.getenv(EnvUtils.DEYE_GRID_FEED_IN_ENERGY_COSTS_JSON, '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_gen_energy_costs_json() -> str:
    val = os.getenv(EnvUtils.DEYE_GEN_ENERGY_COSTS_JSON, '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_energy_cost_currency_code() -> str:
    return os.getenv(EnvUtils.DEYE_ENERGY_COST_CURRENCY_CODE, "USD").strip()[:3]

  @staticmethod
  def get_log_name() -> str:
    log_name = os.getenv(EnvUtils.DEYE_LOG_NAME, '')
    log_name = re.sub(r'[^a-zA-Z0-9-]+', '-', log_name).strip('-')
    if not log_name:
      raise RuntimeError(f"Environment variable '{EnvUtils.DEYE_LOG_NAME}' is not set")
    return log_name

  @staticmethod
  def get_deye_web_register_value_corrections_json() -> str:
    val = os.getenv(EnvUtils.DEYE_WEB_REGISTER_VALUE_CORRECTIONS_JSON, '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_web_section_title_corrections_json() -> str:
    val = os.getenv(EnvUtils.DEYE_WEB_SECTION_TITLE_CORRECTIONS_JSON, '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_web_register_description_replacements_json() -> str:
    val = os.getenv(EnvUtils.DEYE_WEB_REGISTER_DESCRIPTION_REPLACEMENTS_JSON, '{}').strip()
    return val if val else '{}'

  @staticmethod
  def get_deye_web_graphs_base_url() -> str:
    return os.getenv(EnvUtils.DEYE_WEB_GRAPHS_BASE_URL, '').strip()

  @staticmethod
  def is_tests_on() -> bool:
    value = os.getenv(EnvUtils.IS_TEST_RUN, '').strip().lower()
    return value in ('true', 'yes')

  @staticmethod
  def _get_logger_serial(name: str) -> int:
    serial = os.getenv(name, '').strip()

    if not serial:
      raise RuntimeError(f"Environment variable '{name}' is not set")

    if not EnvUtils._is_serial_correct(serial):
      raise RuntimeError(f"Logger serial number '{name}' is invalid")

    return int(serial)

  @staticmethod
  def _get_logger_port(name: str) -> int:
    port = os.getenv(name, '8899').strip()

    if not port:
      raise RuntimeError(f"Environment variable '{name}' is not set")

    if not EnvUtils._is_port_correct(port):
      raise RuntimeError(f"Logger port '{name}' is invalid")

    return int(port)

  @staticmethod
  def _is_serial_correct(serial: str) -> bool:
    return re.fullmatch(r'\d+', serial) is not None

  @staticmethod
  def _is_port_correct(port_num: str) -> bool:
    if not re.fullmatch(r'\d{1,5}', port_num):
      return False
    return 1 <= int(port_num) <= 65535
