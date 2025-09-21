from int_deye_register import IntDeyeRegister
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_utils import to_signed

class SignedIntDeyeRegister(IntDeyeRegister):
  def __init__(
    self,
    address: int,
    name: str,
    description: str,
    suffix: str,
    avg = DeyeRegisterAverageType.none,
  ):
    super().__init__(address, name, description, suffix, avg)

  def read_internal(self, interactor: DeyeModbusInteractor):
    value = to_signed(interactor.read_register(self.address, self.quantity)[0])
    return value
