from typing import List, Optional
from telebot_user import TelebotUser
from deye_registers import DeyeRegisters
from deye_exceptions import DeyeNotImplementedException
from deye_registers_factory import DeyeRegistersFactory

class TelebotBaseUsers:
  registers: Optional[DeyeRegisters] = None

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
    return any(user.id == user_id for user in self.allowed_users)

  def get_allowed_user(self, user_id: int) -> Optional[TelebotUser]:
    for user in self.allowed_users:
      if user.id == user_id:
        return user
    return None

  def is_user_blocked(self, user_id: int) -> bool:
    return any(user.id == user_id for user in self.blocked_users)
