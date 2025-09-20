from typing import List, Union
from telebot_user import TelebotUser
from deye_exceptions import DeyeNotImplementedException

class TelebotBaseUsers:
  @property
  def allowed_users(self) -> List[TelebotUser]:
    raise DeyeNotImplementedException('allowed_users')

  @property
  def blocked_users(self) -> List[TelebotUser]:
    raise DeyeNotImplementedException('blocked_users')

  def is_user_allowed(self, user_id: int) -> bool:
    return any(user.id == user_id for user in self.allowed_users)

  def get_allowed_user(self, user_id: int) -> Union[TelebotUser, None]:
    for user in self.allowed_users:
      if user.id == user_id:
        return user
    return None

  def is_user_blocked(self, user_id: int) -> bool:
    return any(user.id == user_id for user in self.blocked_users)
