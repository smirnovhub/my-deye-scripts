from typing import List

from testable_telebot import TestableTelebot
from solarman_server import AioSolarmanServer

class TelebotBaseTestModule:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot

  def run_tests(self, servers: List[AioSolarmanServer]):
    raise NotImplementedError(f'{self.__class__.__name__}: run_tests() is not implemented')
