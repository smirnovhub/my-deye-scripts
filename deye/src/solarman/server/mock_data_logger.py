import struct

from pysolarmanv5.pysolarmanv5 import CONTROL_CODE, PySolarmanV5

class MockDatalogger(PySolarmanV5):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def _socket_setup(self, *args, **kwargs):
    pass

  def v5_frame_response_encoder(self, modbus_frame):
    """
    Take a modbus RTU frame and encode it as a V5 data logging stick response frame

    :param modbus_frame: Modbus RTU frame
    :type modbus_frame: bytes
    :return: V5 frame
    :rtype: bytearray

    """
    length = 14 + len(modbus_frame)

    self.v5_length = struct.pack("<H", length)
    self.v5_seq = struct.pack("<BB", self.sequence_number, self._get_next_sequence_number())

    v5_header = self._v5_header(length, self._get_response_code(CONTROL_CODE.REQUEST), self.v5_seq)

    v5_payload = bytearray(self.v5_frametype + bytes.fromhex("01") + self.v5_deliverytime + self.v5_powerontime +
                           self.v5_offsettime + modbus_frame)

    v5_frame = v5_header + v5_payload

    return v5_frame + self._v5_trailer(v5_frame)
