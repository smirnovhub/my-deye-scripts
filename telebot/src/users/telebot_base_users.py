import logging

from typing import List, Optional

from deye_utils import DeyeUtils
from telebot_user import TelebotUser
from deye_registers import DeyeRegisters
from deye_exceptions import DeyeNotImplementedException
from deye_registers import DeyeRegisters

class TelebotBaseUsers:
  _instance = None

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      if DeyeUtils.is_tests_on():
        from telebot_test_users import TelebotTestUsers
        cls._instance = super().__new__(TelebotTestUsers) # type: ignore
        cls.__init__(cls._instance)
      else:
        cls._instance = super().__new__(cls) # type: ignore

    return cls._instance

  def __init__(self):
    self.registers = DeyeRegisters()

  @property
  def allowed_users(self) -> List[TelebotUser]:
    raise DeyeNotImplementedException('allowed_users')

  @property
  def blocked_users(self) -> List[TelebotUser]:
    raise DeyeNotImplementedException('blocked_users')

  def is_user_allowed(self, user_id: int) -> bool:
    self._validate_users(self.allowed_users)
    return any(user.id == user_id for user in self.allowed_users)

  def get_allowed_user(self, user_id: int) -> Optional[TelebotUser]:
    for user in self.allowed_users:
      if user.id == user_id:
        return user
    return None

  def is_user_blocked(self, user_id: int) -> bool:
    self._validate_users(self.blocked_users)
    return any(user.id == user_id for user in self.blocked_users)

  def _validate_users(self, users: List[TelebotUser]):
    """Validate that all users in the list have unique IDs."""
    if DeyeUtils.is_tests_on():
      log = logging.getLogger()
      ids = [user.id for user in users]
      duplicates = {i for i in ids if ids.count(i) > 1}
      if duplicates:
        msg = f"ERROR: duplicated user IDs detected: {duplicates}"
        log.info(msg)
        print(msg)
        raise ValueError(msg)
