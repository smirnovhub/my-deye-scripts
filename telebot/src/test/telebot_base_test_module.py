from testable_telebot import TestableTelebot

class TelebotBaseTestModule:
  def __init__(self, bot: TestableTelebot):
    self.bot = bot

  def run_tests(self):
    raise NotImplementedError(f'{self.__class__.__name__}: run_tests() is not implemented')
