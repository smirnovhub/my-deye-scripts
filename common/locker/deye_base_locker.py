from deye_exceptions import DeyeNotImplementedException

class DeyeBaseLocker:
  def acquire(self, timeout: int = 15) -> None:
    raise DeyeNotImplementedException('acquire')

  def release(self) -> None:
    raise DeyeNotImplementedException('release')
