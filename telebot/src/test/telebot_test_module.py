import os
import time
import logging
import logging

from deye_loggers import DeyeLoggers
from telebot_users import TelebotUsers
from deye_exceptions import DeyeKnownException
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule
from deye_test_helper import get_random_by_register_value_type

class TelebotTestModule(TelebotBaseTestModule):
  def run_tests(self):
    users = TelebotUsers()
    loggers = DeyeLoggers()
    registers = DeyeRegistersFactory.create_registers()

    if not loggers.is_test_loggers:
      raise DeyeKnownException('Your loggers are not test loggers')

    logger = loggers.master

    logging.basicConfig(
      level = logging.INFO,
      format = "[%(asctime)s] [%(levelname)s] %(message)s",
      datefmt = "%Y-%m-%d %H:%M:%S",
    )

    server = AioSolarmanServer(
      name = logger.name,
      address = logger.address,
      serial = logger.serial,
      port = logger.port,
    )

    #fake_message = TelebotFakeTestMessage.make(
    #text = f'/master_inverter_info',
    #user_id = users.allowed_users[0].id,
    #)

    #self.bot.process_new_messages([fake_message])

    for register in registers.all_registers:
      if not register.can_write:
        continue

      value = get_random_by_register_value_type(register, skip_zero = True)
      if value is None:
        print(f"Skipping register '{register.name}' with type {type(register).__name__}")
        continue

      print(f"Processing register '{register.name}' with value type {type(register.value).__name__}...")

      fake_message = TelebotFakeTestMessage.make(
        text = f'/{register.name} {value}',
        user_id = users.allowed_users[0].id,
      )

      self.bot.process_new_messages([fake_message])

    time.sleep(15)

    for register in registers.all_registers:
      if not register.can_write:
        continue

      print(f'Checking {register.name}...')

      if not server.is_registers_written(register.address, register.quantity):
        print(f"No changes on the server side after writing '{register.name}'")
        os._exit(1)

    print('All tests passed\n')
    os._exit(0)
