import logging

from typing import List, Optional

from telebot_user import TelebotUser
from deye_registers import DeyeRegisters
from deye_exceptions import DeyeNotImplementedException
from deye_registers_factory import DeyeRegistersFactory

class TelebotBaseUsers:
  _instance = None
  registers: DeyeRegisters

  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      from deye_utils import is_tests_on
      from telebot_test_users import TelebotTestUsers
      if is_tests_on():
        cls._instance = super().__new__(TelebotTestUsers)
        TelebotBaseUsers.registers = None
        cls.__init__(cls._instance)
      else:
        cls._instance = super().__new__(cls)
        TelebotBaseUsers.registers = None

    return cls._instance

  def __init__(self):
    if TelebotBaseUsers.registers is None:
      TelebotBaseUsers.registers = DeyeRegistersFactory.create_registers()
    self.registers = TelebotBaseUsers.registers

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
    from deye_utils import is_tests_on

    if is_tests_on():
      log = logging.getLogger()
      ids = [user.id for user in users]
      duplicates = {i for i in ids if ids.count(i) > 1}
      if duplicates:
        msg = f"ERROR: duplicated user IDs detected: {duplicates}"
        log.info(msg)
        print(msg)
        raise ValueError(msg)
