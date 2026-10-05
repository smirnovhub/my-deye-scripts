import sys
import asyncio
import logging
import signal
import time
import zlib

from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List

from umodbus.functions import (
  ReadHoldingRegisters,
  ReadInputRegisters,
  WriteMultipleRegisters,
)

from pysolarmanv5 import PySolarmanV5Async

from log_utils import LogUtils
from deye_utils import DeyeUtils
from common_utils import CommonUtils
from deye_registers import DeyeRegisters
from solarman_base_server import SolarmanBaseServer
from deye_register_cache_data import DeyeRegisterCacheData
from src.deye_proxy_config import DeyeProxyConfig
from deye_registers_caching_time import deye_registers_caching_time

config = DeyeProxyConfig()

logger = LogUtils.setup_hourly_overwrite_file_logger(
  name = "deye-proxy-main",
  log_dir = f"data/{config.LOG_NAME}",
  log_file_template = "deye-proxy-{0}.log",
)

config.validate_or_exit()

log_level = logging.INFO
if config.LOG_LEVEL in logging._nameToLevel:
  log_level = logging._nameToLevel[config.LOG_LEVEL]

logger.setLevel(log_level)

registers = DeyeRegisters()

class CachingSolarmanProxy(SolarmanBaseServer):
  def __init__(self):
    super().__init__(
      name = "CachingProxy",
      address = config.PROXY_HOST,
      port = config.PROXY_PORT,
      serial = config.LOGGER_FAKE_SERIAL,
      logger = logger,
    )
    self._remote_address = config.LOGGER_HOST
    self._remote_port = config.LOGGER_PORT
    self._remote_serial = config.LOGGER_SERIAL

    self._max_register_count = 120

    # Caches for Holding and Input registers
    self._holding_cache: Dict[int, DeyeRegisterCacheData] = {}
    self._input_cache: Dict[int, DeyeRegisterCacheData] = {}

    # Dedicated lock to serialize all network operations with remote Solarman client
    self._remote_client_lock = asyncio.Lock()

    self._remote_client = PySolarmanV5Async(
      address = self._remote_address,
      serial = self._remote_serial,
      port = self._remote_port,
      logger = logger,
    )

    self.shutdown_event = asyncio.Event()
    self._updater_task = None

  async def stop_server_async(self) -> None:
    if self._updater_task:
      self._updater_task.cancel()
    await super().stop_server_async()

  def _get_register_groups(
    self,
    registers: Dict[int, DeyeRegisterCacheData],
    max_gap: int = 15,
  ) -> List[List[DeyeRegisterCacheData]]:
    groups: List[List[DeyeRegisterCacheData]] = []
    current_group: List[DeyeRegisterCacheData] = []

    sorted_addrs = sorted(registers.keys())

    for addr in sorted_addrs:
      reg = registers[addr]
      if not current_group:
        current_group.append(reg)
        continue

      last_reg = current_group[-1]
      gap = reg.address - (last_reg.address + last_reg.quantity)
      group_start = current_group[0].address
      block_end = reg.address + reg.quantity

      # Split group if gap between registers exceeds limit or block length exceeds maximum
      if gap > max_gap or (block_end - group_start) > self._max_register_count:
        groups.append(current_group)
        current_group = [reg]
      else:
        current_group.append(reg)

    if current_group:
      groups.append(current_group)

    # formatted_groups = []
    # for group in groups:
    #   group_str = ", ".join([f"{reg.address}={reg.quantity}" for reg in group])
    #   formatted_groups.append(f"  [{group_str}]")

    # # Join all groups with newlines and wrap in square brackets
    # grp = "[\n" + ",\n".join(formatted_groups) + "\n]"
    # self._log.info(f'Register groups to read from {self.name}:\n{grp}')

    # Calculate register fetching statistics
    requested_count = len(registers)
    total_fetched_count = sum((group[-1].address + group[-1].quantity - group[0].address) for group in groups)
    junk_count = max(0, total_fetched_count - requested_count)
    junk_percentage = (junk_count / total_fetched_count * 100) if total_fetched_count > 0 else 0.0

    # Log register summary and efficiency metrics
    self._log.info(f"Register fetch summary: {requested_count} requested, {total_fetched_count} total read, "
                   f"junk: {junk_count} ({junk_percentage:.0f}%)")

    return groups

  def _get_caching_time_by_register_address(self, address: int) -> int:
    if address in deye_registers_caching_time:
      reg = deye_registers_caching_time[address]
      return round(reg.caching_time.total_seconds())

    register = next((reg for reg in registers.all_registers if address in reg.addresses), None)
    caching_time = register.caching_time if register else None
    return round(caching_time.total_seconds()) if caching_time else config.CACHE_UPDATE_INTERVAL

  def _update_time_registers_locally(
    self,
    cache: Dict[int, DeyeRegisterCacheData],
  ) -> None:
    time_reg = registers.inverter_system_time_register
    cur_date = datetime.now()

    values = DeyeUtils.to_inv_time([
      cur_date.year - 2000,
      cur_date.month,
      cur_date.day,
      cur_date.hour,
      cur_date.minute,
      cur_date.second,
    ])

    start_addr = time_reg.address
    quantity = time_reg.quantity
    now = time.monotonic()

    for i in range(quantity):
      addr = start_addr + i
      if i < len(values):
        existing = cache.get(addr)
        last_access = existing.last_access_ts if existing else 0.0
        cache[addr] = DeyeRegisterCacheData(
          address = addr,
          quantity = 1,
          caching_time = self._get_caching_time_by_register_address(addr),
          read_ts = now,
          last_access_ts = last_access,
          values = [values[i]],
        )

  def _update_serial_number_registers_locally(
    self,
    cache: Dict[int, DeyeRegisterCacheData],
    serial_number: str,
  ) -> None:
    # Ensure the string is exactly ten characters long
    sn = serial_number.ljust(10, ' ')[:10]

    # Convert pairs of ASCII characters to sixteen-bit register values
    values = []
    for i in range(5):
      high_byte = ord(sn[i * 2])
      low_byte = ord(sn[i * 2 + 1])
      values.append((high_byte << 8) | low_byte)

    # Serial number occupies five registers starting from address three
    start_addr = 3
    quantity = 5
    now = time.monotonic()

    for i in range(quantity):
      addr = start_addr + i
      existing = cache.get(addr)
      last_access = existing.last_access_ts if existing else 0.0
      cache[addr] = DeyeRegisterCacheData(
        address = addr,
        quantity = 1,
        caching_time = self._get_caching_time_by_register_address(addr),
        read_ts = now,
        last_access_ts = last_access,
        values = [values[i]],
      )

  async def _update_cache_type(
    self,
    cache: Dict[int, DeyeRegisterCacheData],
    read_func: Callable[[int, int], Awaitable[Any]],
    cache_type_name: str,
  ):
    # Take snapshot of expired cache items under lock
    # We do not hold the lock during network operations
    if not cache:
      return

    now = time.monotonic()
    cache_snapshot: Dict[int, DeyeRegisterCacheData] = {}

    time_reg = registers.inverter_system_time_register
    time_reg_start_addr = time_reg.address
    time_reg_end_addr = time_reg_start_addr + time_reg.quantity

    for addr, data in cache.items():
      # Exclude time registers from remote inverter polling
      if time_reg_start_addr <= addr < time_reg_end_addr:
        continue

      # Keep entry only if caching time has expired
      if (now - data.read_ts) >= data.caching_time:
        cache_snapshot[addr] = data

    if not cache_snapshot:
      return

    # Output all expired addresses from cache snapshot at once
    expired_str = ", ".join(str(addr) for addr in sorted(cache_snapshot.keys()))
    self._log.info(f"Expired registers: {expired_str}")

    groups = self._get_register_groups(cache_snapshot)

    for group in groups:
      start_addr = group[0].address
      last_reg = group[-1]
      block_end = last_reg.address + last_reg.quantity
      quantity_to_read = block_end - start_addr

      addresses_str = ", ".join(str(addr) for addr in range(start_addr, start_addr + quantity_to_read))
      self._log.info(f"Update registers from inverter: {addresses_str}")

      try:
        # Fetch contiguous block from the real inverter
        values = await read_func(start_addr, quantity_to_read)
      except Exception as e:
        self._log.error(f"Failed to read {cache_type_name} group starting at {start_addr}: {e}")
        raise

      now = time.monotonic()
      for reg in group:
        offset = reg.address - start_addr
        if offset < len(values):
          existing = cache.get(reg.address)
          last_access = existing.last_access_ts if existing else 0.0
          cache[reg.address] = DeyeRegisterCacheData(
            address = reg.address,
            quantity = 1,
            caching_time = self._get_caching_time_by_register_address(reg.address),
            read_ts = now,
            last_access_ts = last_access,
            values = [values[offset]],
          )

  async def _background_updater(self):
    while not self.shutdown_event.is_set():
      try:
        await asyncio.sleep(config.CACHE_UPDATE_INTERVAL)

        # Purge cache items that have not been accessed for more than purge timeout
        now = time.monotonic()
        inactive_holding = [
          addr for addr, item in self._holding_cache.items()
          if (now - item.last_access_ts) >= config.CACHE_PURGE_TIMEOUT
        ]

        if inactive_holding:
          addresses_str = ", ".join(str(addr) for addr in sorted(inactive_holding))
          self._log.info(f"Purge inactive holding registers: {addresses_str}")

          for addr in inactive_holding:
            del self._holding_cache[addr]

        now = time.monotonic()
        inactive_input = [
          addr for addr, item in self._input_cache.items() if (now - item.last_access_ts) >= config.CACHE_PURGE_TIMEOUT
        ]

        if inactive_input:
          addresses_str = ", ".join(str(addr) for addr in sorted(inactive_input))
          self._log.info(f"Purge inactive input registers: {addresses_str}")

          for addr in inactive_input:
            del self._input_cache[addr]

        # Acquire client lock for the entire polling sequence
        async with self._remote_client_lock:
          await self._remote_client.connect()
          try:
            # Update Holding Registers
            await self._update_cache_type(
              cache = self._holding_cache,
              read_func = self._remote_client.read_holding_registers,
              cache_type_name = "holding",
            )

            # Update Input Registers
            await self._update_cache_type(
              cache = self._input_cache,
              read_func = self._remote_client.read_input_registers,
              cache_type_name = "input",
            )
          finally:
            try:
              await self._remote_client.disconnect()
            except Exception as e:
              self._log.error(f"Error disconnecting from remote client during background updater: {e}")

      except asyncio.CancelledError:
        break
      except Exception as e:
        self._log.error(f"Error in background updater loop: {e}")

  async def _get_or_fetch_registers(
    self,
    cache: Dict[int, DeyeRegisterCacheData],
    read_func,
    start_addr: int,
    quantity: int,
    client_ip: str,
    client_port: int,
  ) -> List[int]:
    missing = False

    # Check if any requested address is missing in cache
    for addr in range(start_addr, start_addr + quantity):
      if addr not in cache:
        missing = True
        break

    # If cache miss occurred, fetch data immediately from inverter
    if missing:
      try:
        # Synchronize access to physical client across concurrent client calls
        missing = False

        # Double check if any requested address is missing in cache after acquiring the lock
        for addr in range(start_addr, start_addr + quantity):
          if addr not in cache:
            missing = True
            break

        if missing:
          addresses_str = ", ".join(str(addr) for addr in range(start_addr, start_addr + quantity))
          self._log.warning(f"{client_ip}:{client_port} Fetching missing registers from inverter: {addresses_str}")

          async with self._remote_client_lock:
            await self._remote_client.connect()
            try:
              fetched_values = await read_func(start_addr, quantity)
            finally:
              try:
                await self._remote_client.disconnect()
              except Exception as e:
                self._log.error(f"Error disconnecting from remote client after fetching "
                                f"missing registers starting at {start_addr}: {e}")

          now = time.monotonic()
          for i, val in enumerate(fetched_values):
            reg_addr = start_addr + i
            existing = cache.get(reg_addr)
            last_access = existing.last_access_ts if existing else 0.0
            cache[reg_addr] = DeyeRegisterCacheData(
              address = reg_addr,
              quantity = 1,
              caching_time = self._get_caching_time_by_register_address(reg_addr),
              read_ts = now,
              last_access_ts = last_access,
              values = [val],
            )

      except Exception as e:
        self._log.error(f"Failed to fetch missing registers starting at {start_addr}: {e}")

    # Retrieve values from cache and recreate object with updated last access timestamp
    values: List[int] = []

    now = time.monotonic()
    for addr in range(start_addr, start_addr + quantity):
      cached_item = cache.get(addr)
      if cached_item:
        cache[addr] = DeyeRegisterCacheData(
          address = cached_item.address,
          quantity = cached_item.quantity,
          caching_time = cached_item.caching_time,
          read_ts = cached_item.read_ts,
          last_access_ts = now,
          values = cached_item.values,
        )
      # Use 0 as fallback only if inverter connection failed
      values.extend(cached_item.values if cached_item else [0])

    return values

  async def on_read_holding_registers(
    self,
    func: ReadHoldingRegisters,
    client_ip: str,
    client_port: int,
  ) -> bytes:
    start_addr = func.starting_address
    quantity = func.quantity

    if start_addr is None or quantity is None:
      raise ValueError("ReadHoldingRegisters request missing starting_address or quantity")

    # Update local virtual registers prior to reading cache
    self._update_time_registers_locally(self._holding_cache)
    self._update_serial_number_registers_locally(
      cache = self._holding_cache,
      serial_number = self.hash_crc32_str(config.LOGGER_FAKE_SERIAL),
    )

    values = await self._get_or_fetch_registers(
      cache = self._holding_cache,
      read_func = self._remote_client.read_holding_registers,
      start_addr = start_addr,
      quantity = quantity,
      client_ip = client_ip,
      client_port = client_port,
    )

    addresses_str = ", ".join(str(addr) for addr in range(start_addr, start_addr + quantity))
    self._log.info(f"{client_ip}:{client_port} Read holding registers: {addresses_str}")

    return func.create_response_pdu(values)

  async def on_read_input_registers(
    self,
    func: ReadInputRegisters,
    client_ip: str,
    client_port: int,
  ) -> bytes:
    start_addr = func.starting_address
    quantity = func.quantity

    if start_addr is None or quantity is None:
      raise ValueError("ReadInputRegisters request missing starting_address or quantity")

    values = await self._get_or_fetch_registers(
      cache = self._input_cache,
      read_func = self._remote_client.read_input_registers,
      start_addr = start_addr,
      quantity = quantity,
      client_ip = client_ip,
      client_port = client_port,
    )

    addresses_str = ", ".join(str(addr) for addr in range(start_addr, start_addr + quantity))
    self._log.info(f"{client_ip}:{client_port} Read input registers: {addresses_str}")

    return func.create_response_pdu(values)

  async def on_write_multiple_registers(
    self,
    func: WriteMultipleRegisters,
    client_ip: str,
    client_port: int,
  ) -> bytes:
    start_addr = func.starting_address
    values = func.values

    if start_addr is None or values is None:
      raise ValueError("WriteMultipleRegisters request missing starting_address or values")

    # # Send write operation directly to the device
    # await self._remote_client.write_multiple_holding_registers(start_addr, values)

    # # Update cache immediately so subsequent reads don't serve stale
    # # data before the background updater catches up
    # async with self._holding_lock:
    #   for i, val in enumerate(values):
    #     addr = start_addr + i
    #     if addr in self._holding_cache:
    #       self._holding_cache[addr].value = val
    #     else:
    #       self._holding_cache[addr] = DeyeRegisterCacheData(address = addr, quantity = 1, value = val)

    self._log.warning(f"{client_ip}:{client_port} Trying to write registers starting at "
                      f"{start_addr} with values {values}, but this proxy is read-only")

    return func.create_response_pdu()

  def hash_crc32_str(self, number: int) -> str:
    num_str = str(number)
    length = len(num_str)

    # Calculate CRC32 checksum
    raw_crc = zlib.crc32(num_str.encode())

    # Format with exact digit count using leading zeros
    return f"{raw_crc % (10 ** length):0{length}d}"

  def handle_exit(self, sig_num: int) -> None:
    logger.info(f"Received signal {sig_num}. Shutting down gracefully...")
    self.shutdown_event.set()

  async def run(self) -> None:
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
      try:
        loop.add_signal_handler(sig, self.handle_exit, sig)
      except NotImplementedError:
        signal.signal(sig, lambda s, f: self.handle_exit(s))

    external_ip = CommonUtils.get_external_ip(config.LOGGER_HOST, config.LOGGER_PORT)
    actual_ip = external_ip if external_ip else config.PROXY_HOST

    log_level_name = logging._levelToName[log_level]

    logger.info("------- Deye Read-Only Caching Proxy Server started -------")
    logger.info(f"Target logger         : {config.LOGGER_HOST}:{config.LOGGER_PORT}")
    logger.info(f"Logger real serial    : {config.LOGGER_SERIAL}")
    logger.info(f"Logger fake serial    : {config.LOGGER_FAKE_SERIAL}")
    logger.info(f"Listening on          : {actual_ip}:{config.PROXY_PORT}")
    logger.info(f"Cache update interval : {config.CACHE_UPDATE_INTERVAL}s")
    logger.info(f"Cache purge timeout   : {config.CACHE_PURGE_TIMEOUT}s")
    logger.info(f"Read only             : {config.READ_ONLY}")
    logger.info(f"Log level             : {log_level_name}")
    logger.info("-----------------------------------------------------------")

    self._updater_task = asyncio.create_task(self._background_updater())

    await self.shutdown_event.wait()

    logger.info("Shutting down caching proxy server...")

    if self._updater_task:
      self._updater_task.cancel()
      try:
        await self._updater_task
      except asyncio.CancelledError:
        pass

    await super().stop_server_async()

    logger.info("Server stopped.")

    for handler in logging.getLogger().handlers:
      handler.flush()

    sys.stdout.flush()
    sys.stderr.flush()

async def main_read_only_cache() -> None:
  proxy = CachingSolarmanProxy()
  await proxy.run()
