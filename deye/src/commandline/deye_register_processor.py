import argparse

from typing import Any, List, Type
from deye_logger import DeyeLogger
from deye_register import DeyeRegister
from raising_thread import RaisingThread
from deye_exceptions import DeyeKnownException
from deye_modbus_interactor import DeyeModbusInteractor
from deye_register_average_type import DeyeRegisterAverageType
from deye_registers_factory import DeyeRegistersFactory
from deye_utils import get_reraised_exception

class DeyeRegisterProcessor:
  def __init__(self):
    self.interactors: List[DeyeModbusInteractor] = []
    self.master_interactor: DeyeModbusInteractor = None
    self.registers = DeyeRegistersFactory.create_registers()

  def get_arg_name(self, register: DeyeRegister, action: str) -> str:
    return f'--{action}-{register.name.replace("_", "-")}'

  def get_arg_desc(self, register: DeyeRegister, action: str) -> str:
    return f'{action} {register.name.replace("_", " ")}' if not register.suffix else f'{action} {register.name.replace("_", " ")}, {register.suffix.replace("%", "%%")}'

  def get_write_limit_desc(self, register: DeyeRegister) -> str:
    return f'from {register.min_value} to {register.max_value}'

  def get_register_type(self, register: DeyeRegister) -> Type[Any]:
    return type(register.value)

  def add_command_line_parameters(self, parser: argparse.ArgumentParser):
    try:
      for register in self.registers.read_only_registers:
        parser.add_argument(self.get_arg_name(register, 'get'),
                            action = 'store_true',
                            help = self.get_arg_desc(register, 'get'))

      for register in self.registers.read_write_registers:
        set_help = f'{self.get_arg_desc(register, "set")} ({self.get_write_limit_desc(register)})' if type(
          register.value) is not str else f'{self.get_arg_desc(register, "set")}'
        parser.add_argument(self.get_arg_name(register, 'get'),
                            action = 'store_true',
                            help = self.get_arg_desc(register, 'get'))
        parser.add_argument(self.get_arg_name(register, 'set'),
                            metavar = register.suffix,
                            type = self.get_register_type(register),
                            help = set_help)

      for register in self.registers.forecast_registers:
        parser.add_argument(self.get_arg_name(register, 'get'),
                            action = 'store_true',
                            help = self.get_arg_desc(register, 'get'))

    except Exception as e:
      raise get_reraised_exception(e, 'Error while adding parameters') from e

  def check_parameters(self, parser: argparse.ArgumentParser, args: argparse.Namespace) -> bool:
    try:
      for register in self.registers.read_write_registers:
        arg_name = f'set_{register.name}'
        if hasattr(args, arg_name):
          value = getattr(args, arg_name)
          if value != None and type(value) is not str and (value < register.min_value or value > register.max_value):
            parser.error(f'argument --{arg_name.replace("_", "-")}: should be {self.get_write_limit_desc(register)}')
            return False

      return True
    except Exception as e:
      raise get_reraised_exception(e, 'Error while checking parameters') from e

  def process_parameters(self, args: argparse.Namespace):
    if len(self.interactors) < 2 or args.only_accumulated == False:
      for interactor in self.interactors:
        for register in self.get_registers_to_process(args):
          try:
            if interactor.is_master or register.avg_type != DeyeRegisterAverageType.only_master:
              value = register.read([interactor])
              addr_list = ' ' + str(register.addresses) if args.print_addresses else ''
              print(f'{interactor.name}_{register.name}{addr_list} = {value} {register.suffix}')
          except Exception as e:
            raise get_reraised_exception(e,
                                         f'Error while reading register {register.name} from {interactor.name}') from e

    if len(self.interactors) > 1:
      for register in self.get_registers_to_process(args):
        try:
          if register.can_accumulate:
            value = register.read(self.interactors)
            addr_list = ' ' + str(register.addresses) if args.print_addresses else ''
            print(f'all_{register.name}{addr_list} = {value} {register.suffix}')
        except Exception as e:
          raise get_reraised_exception(e, f'Error while reading register {register.name}') from e

    for register in self.registers.read_write_registers:
      try:
        arg_name = f'set_{register.name}'
        if hasattr(args, arg_name):
          value = getattr(args, arg_name)
          if value != None:
            if self.master_interactor == None:
              raise DeyeKnownException('You can write only to master inverter')
            register.write(self.master_interactor, value)
            addr_list = ' ' + str(register.addresses) if args.print_addresses else ''
            print(f'{self.master_interactor.name}_{register.name}{addr_list} = {value} {register.suffix}')
      except Exception as e:
        raise get_reraised_exception(e, f'Error while writing register {register.name}') from e

  def enqueue_registers(self, args: argparse.Namespace, loggers: List[DeyeLogger]):
    for logger in loggers:
      try:
        interactor = DeyeModbusInteractor(logger = logger,
                                          socket_timeout = 10,
                                          caching_time = args.caching_time,
                                          verbose = args.verbose_output == True)
        self.interactors.append(interactor)
        if interactor.is_master:
          self.master_interactor = interactor
      except Exception as e:
        raise get_reraised_exception(e, f'Error while creating DeyeModbusInteractor({logger.name})') from e

    for interactor in self.interactors:
      for register in self.get_registers_to_process(args):
        try:
          register.enqueue(interactor)
        except Exception as e:
          raise get_reraised_exception(
            e, f'Error while enqueue register {register.name} to interactor {interactor.name}') from e

  def get_registers_to_process(self, args: argparse.Namespace) -> List[DeyeRegister]:
    result = []

    if args.get_all == True:
      result.extend(self.registers.all_registers)

    if args.get_all_read_only == True:
      result.extend(self.registers.read_only_registers)

    if args.get_all_read_write == True:
      result.extend(self.registers.read_write_registers)

    if args.forecast == True:
      result.extend(self.registers.forecast_registers)

    all_registers = self.registers.all_registers + self.registers.forecast_registers

    for register in all_registers:
      arg_name = f'get_{register.name}'
      value = getattr(args, arg_name)
      if value == True:
        result.append(register)

    if args.test == True:
      result.extend(self.registers.test_registers)

    return result

  def process_registers(self):
    try:
      tasks: List[RaisingThread] = []
      for interactor in self.interactors:
        tasks.append(RaisingThread(target = interactor.process_enqueued_registers))

      for task in tasks:
        task.start()

      for task in tasks:
        task.join()

    except Exception as e:
      raise get_reraised_exception(e, 'Error while reading registers') from e

  def disconnect(self):
    for interactor in self.interactors:
      try:
        interactor.disconnect()
      except Exception as e:
        raise get_reraised_exception(e, f'Error while disconnecting {interactor.name}') from e
