from deye_base_locker import DeyeBaseLocker

class DeyeEmptyLocker(DeyeBaseLocker):
  def acquire(self, timeout: float = 15) -> None:
    pass

  def release(self) -> None:
    pass
