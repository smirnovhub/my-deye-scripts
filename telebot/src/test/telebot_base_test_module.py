import time
import logging

from typing import Callable, List, Optional

from deye_loggers import DeyeLoggers
from testable_telebot import TestableTelebot
from solarman_server import AioSolarmanServer
from deye_exceptions import DeyeKnownException
from deye_utils import get_test_retry_count

class TelebotBaseTestModule:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot
    self.log = logging.getLogger()
    self.loggers = DeyeLoggers()

  def run_tests(self, servers: List[AioSolarmanServer]):
    raise NotImplementedError(f'{self.__class__.__name__}: run_tests() is not implemented')

  def call_with_retry(self, func: Callable, *args, **kwargs):
    """
    Calls a function repeatedly until it succeeds or retries are exhausted.

    :param func: The function to call.
    :param args: Positional arguments to pass to func.
    :param kwargs: Keyword arguments to pass to func.
    :raises Exception: Re-raises the last exception if all retries fail.
    """
    retry_delay = 1.0
    retry_count = get_test_retry_count()
    last_exception: Optional[Exception] = None

    owner = getattr(func, "__self__", None)
    class_name = f'{owner.__class__.__name__}.' if owner else ''
    func_name = func.__name__

    for i in range(retry_count):
      try:
        return func(*args, **kwargs)
      except Exception as e:
        last_exception = e
        self.log.info(f"Call to {class_name}{func_name} failed: {e}. "
                      f"Retrying in {retry_delay}s (attempt {i + 1}/{retry_count})...")
        time.sleep(retry_delay)
    else:
      self.log.info(f"Retry count {retry_count} exceeded for {class_name}{func_name}")
      if last_exception is not None:
        raise last_exception

  def error(self, message: str):
    self.log.info(message)
    raise DeyeKnownException(message)
