import io
import os
import sys
import time
import asyncio
import logging

from pathlib import Path
from typing import Any, Dict, List
from contextlib import redirect_stdout

base_path = '../..'
current_path = Path(__file__).parent.resolve()
modules_path = (current_path / base_path / 'modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(
  current_path,
  [
    'src',
    os.path.join(base_path, 'deye'),
    os.path.join(base_path, 'common'),
  ],
)

from deye_utils import DeyeUtils
from deye_test_utils import DeyeTestUtils
from deye_loggers import DeyeLoggers
from deye_registers import DeyeRegisters
from solarman_test_server import SolarmanTestServer
from deye_test_helper import DeyeTestHelper
from deye_test_helper import DeyeRegisterRandomValue
from deye_register_average_type import DeyeRegisterAverageType

from deye import main as deye_main

async def main():
  DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)

  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  log = logging.getLogger()
  loggers = DeyeLoggers()
  registers = DeyeRegisters()

  if not loggers.is_test_loggers:
    log.error('ERROR: your loggers are not test loggers')
    sys.exit(1)

  servers: List[SolarmanTestServer] = []

  for logger in loggers.loggers:
    server = SolarmanTestServer(
      name = logger.name,
      address = logger.address,
      serial = logger.serial,
      port = logger.port,
    )

    servers.append(server)

  if not await DeyeTestUtils.wait_for_solarman_servers_ready(loggers.loggers):
    return

  registers_to_skip = [
    registers.grid_state_register.name,
    registers.inverter_system_time_diff_register.name,
    registers.time_of_use_register.name,
  ]

  def generate_random_register_values(server: SolarmanTestServer) -> Dict[str, Any]:
    random_values: Dict[str, Any] = {}
    randoms: List[DeyeRegisterRandomValue] = []

    server.clear_registers_status()

    for register in registers.all_registers:
      if register.name in registers_to_skip:
        log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
        continue

      if register.avg_type == DeyeRegisterAverageType.only_master and server.name != loggers.master.name:
        log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
        continue

      log.info(f"Processing register '{register.name}' with type {type(register).__name__}")

      random_value = DeyeTestHelper.get_random_by_register_type(register, randoms)
      if random_value is None:
        log.info(f"Register '{register.name}' is skipped")
        continue

      randoms.append(random_value)
      random_values[register.name] = random_value.value

      suffix = f' {register.suffix}'.rstrip()

      log.info(f"Generated random value for register '{register.name}' is {random_value.value}{suffix}...")

      if random_value.register.address > 0:
        server.set_register_values(random_value.register.addresses, random_value.values)

    return random_values

  async def run_command(cmds: List[str]) -> str:
    fake_args = [
      "deye",
      '-v',
      '--connection-timeout',
      '1',
      '-c 0',
    ]

    fake_args.extend(cmds)

    log.info(f'Command to execute: {" ".join(fake_args)}')

    for i in range(10):
      old_argv = sys.argv
      sys.argv = fake_args

      output_buffer = io.StringIO()

      try:
        # Redirect all print() calls to the buffer
        with redirect_stdout(output_buffer):
          try:
            await deye_main()
          except SystemExit:
            pass
      except Exception as e:
        log.error(f'An exception occurred: {e}. Retrying...')
        await asyncio.sleep(1)
        continue
      finally:
        # Restore original argv
        sys.argv = old_argv

      output = output_buffer.getvalue().strip()

      log.info(f'Command output: {output}')

      if 'exception' not in output and 'error' not in output:
        return output

      log.error('An exception occurred. Retrying...')
      await asyncio.sleep(1)
    else:
      log.error('Retry count exceeded')
      sys.exit(1)

  def check_results(server: SolarmanTestServer, output: str, random_values: Dict[str, Any]):
    for register in registers.all_registers:
      if register.name in registers_to_skip:
        log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
        continue

      if (register.avg_type == DeyeRegisterAverageType.only_master
          or register.avg_type == DeyeRegisterAverageType.fake_accumulate) and server.name != loggers.master.name:
        log.info(f"Skipped register '{register.name}' with type {type(register).__name__}")
        continue

      if not server.is_registers_readed(register.address, register.quantity):
        log.error(f"No request for read on the server side after reading '{register.name}'")
        sys.exit(1)

      suffix = f' {register.suffix}'.rstrip()
      random_value = random_values.get(register.name, 0)
      name = f'{server.name}_{register.name} = {random_value}{suffix}'.strip()

      log.info(f"Finding '{name}'...")

      if name not in output:
        log.error('Register or value not found. Test failed')
        sys.exit(1)
      else:
        log.info('Register and value found')

  for server in servers:
    random_values = generate_random_register_values(server)
    output = await run_command([f"--get-{r.name.replace('_', '-')}"
                                for r in registers.all_registers] + [f'-i {server.name}'])
    check_results(server, output, random_values)

    random_values = generate_random_register_values(server)
    output = await run_command(['-a', f'-i {server.name}'])
    check_results(server, output, random_values)

    log.info('All registers and values found. Test is ok')

if __name__ == "__main__":
  asyncio.run(main())
