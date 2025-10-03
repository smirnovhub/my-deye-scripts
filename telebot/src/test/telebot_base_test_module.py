import logging

from typing import List

from testable_telebot import TestableTelebot
from solarman_server import AioSolarmanServer
from deye_exceptions import DeyeKnownException

class TelebotBaseTestModule:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot
    self.log = logging.getLogger()

  def run_tests(self, servers: List[AioSolarmanServer]):
    raise NotImplementedError(f'{self.__class__.__name__}: run_tests() is not implemented')

  def error(self, message: str):
    self.log.info(message)
    raise DeyeKnownException(message)
