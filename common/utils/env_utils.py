import os
import re

class EnvUtils:
  @staticmethod
  def get_master_logger_host() -> str:
    return os.getenv('DEYE_MASTER_LOGGER_HOST', '').strip()

  @staticmethod
  def get_master_logger_serial() -> int:
    return EnvUtils.get_logger_serial('DEYE_MASTER_LOGGER_SERIAL')

  @staticmethod
  def get_master_logger_port() -> int:
    return EnvUtils.get_logger_port('DEYE_MASTER_LOGGER_PORT')

  @staticmethod
  def get_slave_logger_host(num: int) -> str:
    return os.getenv(f'DEYE_SLAVE{num}_LOGGER_HOST', '').strip()

  @staticmethod
  def get_slave_logger_serial(num: int) -> int:
    return EnvUtils.get_logger_serial(f'DEYE_SLAVE{num}_LOGGER_SERIAL')

  @staticmethod
  def get_slave_logger_port(num: int) -> int:
    return EnvUtils.get_logger_port(f'DEYE_SLAVE{num}_LOGGER_PORT')

  @staticmethod
  def get_logger_serial(name: str) -> int:
    serial = os.getenv(name, '').strip()

    if not EnvUtils.is_serial_correct(serial):
      raise RuntimeError(f'Invalid serial for logger: {name}')

    return int(serial)

  @staticmethod
  def get_logger_port(name: str) -> int:
    port = os.getenv(name, '8899').strip()

    if not EnvUtils.is_port_correct(port):
      raise RuntimeError(f'Invalid port for logger: {name}')

    return int(port)

  @staticmethod
  def is_serial_correct(serial: str) -> bool:
    return re.fullmatch(r'\d+', serial) is not None

  @staticmethod
  def is_port_correct(port_num: str) -> bool:
    if not re.fullmatch(r'\d{1,5}', port_num):
      return False
    return 1 <= int(port_num) <= 65535

  @staticmethod
  def set_remote_cache_server_url(server: str):
    os.environ['REMOTE_CACHE_SERVER_URL'] = server

  @staticmethod
  def get_remote_cache_server_url() -> str:
    return os.getenv('REMOTE_CACHE_SERVER_URL', '').strip()

  @staticmethod
  def get_mikrotik_server_url() -> str:
    return os.getenv('MIKROTIK_SERVER_URL', '').strip()

  @staticmethod
  def get_scheduler_server_url() -> str:
    return os.getenv('SCHEDULER_SERVER_URL', '').strip()

  @staticmethod
  def get_telegram_bot_api_test_token() -> str:
    return os.getenv('BOT_API_TEST_TOKEN', '').strip()

  @staticmethod
  def get_log_name(default: str) -> str:
    log_name = os.getenv("DEYE_LOG_NAME", default)
    return re.sub(r'[^a-zA-Z0-9-]+', '-', log_name).strip('-')

  @staticmethod
  def is_tests_on() -> bool:
    value = os.getenv('IS_TEST_RUN', '').strip().lower()
    return value in ('true', 'yes')

  @staticmethod
  def turn_tests_on():
    os.environ['IS_TEST_RUN'] = 'true'
