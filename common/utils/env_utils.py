import os

class EnvUtils:
  @staticmethod
  def is_remote_cache_on() -> bool:
    value = os.getenv('USE_REMOTE_CACHE', '').strip().lower()
    return value in ('true', 'yes')

  @staticmethod
  def turn_remote_cache_on(server: str):
    os.environ['USE_REMOTE_CACHE'] = 'true'
    os.environ['REMOTE_CACHE_SERVER'] = server

  @staticmethod
  def get_remote_cache_server() -> str:
    return os.getenv('REMOTE_CACHE_SERVER', '').strip()

  @staticmethod
  def get_telegram_bot_api_test_token() -> str:
    return os.getenv('BOT_API_TEST_TOKEN', '').strip()

  @staticmethod
  def is_tests_on() -> bool:
    value = os.getenv('IS_TEST_RUN', '').strip().lower()
    return value in ('true', 'yes')

  @staticmethod
  def turn_tests_on():
    os.environ['IS_TEST_RUN'] = 'true'
