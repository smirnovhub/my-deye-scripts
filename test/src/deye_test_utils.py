import os

class DeyeTestUtils:
  @staticmethod
  def setup_test_environment():
    os.environ['IS_TEST_RUN'] = 'true'

    num = 1
    port = 7000

    os.environ['DEYE_MASTER_LOGGER_HOST'] = '127.0.0.1'
    os.environ['DEYE_MASTER_LOGGER_SERIAL'] = str(num)
    os.environ['DEYE_MASTER_LOGGER_PORT'] = str(port)

    for i in range(1, 4):
      num += 1
      port += 1
      os.environ[f'DEYE_SLAVE{i}_LOGGER_HOST'] = '127.0.0.1'
      os.environ[f'DEYE_SLAVE{i}_LOGGER_SERIAL'] = str(num)
      os.environ[f'DEYE_SLAVE{i}_LOGGER_PORT'] = str(port)
