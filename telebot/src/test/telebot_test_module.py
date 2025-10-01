import os
import time
import random
import logging
import logging

from datetime import datetime, timedelta
from deye_loggers import DeyeLoggers
from deye_base_enum import DeyeBaseEnum
from telebot_users import TelebotUsers
from deye_exceptions import DeyeKnownException
from deye_registers_factory import DeyeRegistersFactory
from solarman_server import AioSolarmanServer
from telebot_fake_test_message import TelebotFakeTestMessage
from telebot_base_test_module import TelebotBaseTestModule

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

    for register in registers.all_registers:
      if not register.can_write:
        continue

      if isinstance(register.value, DeyeBaseEnum):
        valid_values = [v for v in type(register.value) if v.value == 1]
        value = random.choice(valid_values)
      else:
        continue

      print(f'Processing {register.name}...')

      fake_message = TelebotFakeTestMessage.make(
        text = f'/{register.name} {value}',
        user_id = users.allowed_users[0].id,
      )

      self.bot.process_new_messages([fake_message])

      yes_message = TelebotFakeTestMessage.make(
        text = 'yes',
        user_id = users.allowed_users[0].id,
      )

      time.sleep(3)
      print('send yes')
      self.bot.process_new_messages([yes_message])

    for register in registers.all_registers:
      if not register.can_write:
        continue

      value = ''
      if isinstance(register.value, int):
        while True:
          value = round(random.uniform(register.min_value, register.max_value))
          if value != 0:
            break
      elif isinstance(register.value, float):
        while True:
          value = round(random.uniform(register.min_value, register.max_value), 2)
          if abs(value) > 0.1:
            break
      elif isinstance(register.value, datetime):
        start = datetime(2000, 1, 1)
        end = datetime.now()
        random_date = start + timedelta(seconds = random.randint(0, int((end - start).total_seconds())))
        value = random_date.strftime("%Y-%m-%d %H:%M:%S")
      elif isinstance(register.value, DeyeBaseEnum):
        continue

      print(f'Processing {register.name}...')

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
        print(f"########### No changes on the server side after writing '{register.name}'")
        os._exit(1)

    print('All tests passed')
    os._exit(0)
