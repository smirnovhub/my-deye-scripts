from deye_logger import DeyeLogger

class DeyeLoggers:
  def __init__(self):
    self._loggers = {
      'master': DeyeLogger(name ='master', ip = '192.168.0.73', serial = 1234567890),
#      'slave1': DeyeLogger(name = 'slave1', ip = '192.168.0.75', serial = 1234567890),
    }

  @property
  def master(self):
    return self._loggers['master']

  @property
  def slave1(self):
    return self._loggers.get('slave1', None)

  @property
  def loggers(self):
    return self._loggers.copy()

  @property
  def loggers_list(self):
    return list(self._loggers.values())
