import asyncio
import logging
import time

from typing import Dict, List
from pysolarmanv5 import PySolarmanV5Async
from deye_registers import DeyeRegisters
from deye_register_cache_data import DeyeRegisterCacheData
from src.deye_proxy_config import DeyeProxyConfig
from src.deye_register_type_enum import DeyeRegisterType
from src.deye_virtual_registers import DeyeVirtualRegisterProvider
from src.deye_registers_caching_time import DeyeRegistersCachingTimeHolder

class DeyeRegistersCache:
  def __init__(
    self,
    type: DeyeRegisterType,
    config: DeyeProxyConfig,
    logger_client_lock: asyncio.Lock,
    logger: logging.Logger,
  ):
    self._register_type = type
    self._log = logger
    self._config = config
    self._max_register_count_in_group = 120
    self._registers = DeyeRegisters()

    self._logger_client = PySolarmanV5Async(
      address = config.LOGGER_HOST,
      serial = config.LOGGER_SERIAL,
      port = config.LOGGER_PORT,
      logger = logger,
    )

    self._logger_client_lock = logger_client_lock
    self._registers_cache: Dict[int, DeyeRegisterCacheData] = {}
    self._virtual_provider = DeyeVirtualRegisterProvider(serial = config.LOGGER_FAKE_SERIAL)
    self._caching_time_holder = DeyeRegistersCachingTimeHolder(config = config)

  def _update_virtual_registers(
    self,
    client_ip: str,
    client_port: int,
  ) -> None:
    now = time.monotonic()

    for virtual_register in self._virtual_provider.virtual_registers:
      caching_time = round(virtual_register.caching_time.total_seconds())

      # Skip update if cached data for this virtual register is still valid
      existing_start = self._registers_cache.get(virtual_register.start_address)
      if existing_start is not None and (now - existing_start.read_ts) < existing_start.caching_time:
        continue

      values = virtual_register.generate_values()
      start_address = virtual_register.start_address
      quantity = len(values)

      addresses_str = ", ".join(str(addr) for addr in range(start_address, start_address + quantity))
      self._log.info(f"{client_ip}:{client_port} Update virtual {self._register_type.name.lower()} "
                     f"registers ({virtual_register.__class__.__name__}): {addresses_str}")

      for i, val in enumerate(values):
        address = start_address + i
        existing = self._registers_cache.get(address)
        last_access = existing.last_access_ts if existing else now
        self._registers_cache[address] = DeyeRegisterCacheData(
          address = address,
          quantity = 1,
          caching_time = caching_time,
          read_ts = now,
          last_access_ts = last_access,
          values = [val],
        )

  def _get_register_groups(
    self,
    registers_dict: Dict[int, DeyeRegisterCacheData],
    max_gap: int = 15,
  ) -> List[List[DeyeRegisterCacheData]]:
    groups: List[List[DeyeRegisterCacheData]] = []
    current_group: List[DeyeRegisterCacheData] = []

    sorted_addrs = sorted(registers_dict.keys())

    for addr in sorted_addrs:
      reg = registers_dict[addr]
      if not current_group:
        current_group.append(reg)
        continue

      last_reg = current_group[-1]
      gap = reg.address - (last_reg.address + last_reg.quantity)
      group_start = current_group[0].address
      block_end = reg.address + reg.quantity

      # Split group if gap between registers exceeds limit or block length exceeds maximum
      if gap > max_gap or (block_end - group_start) > self._max_register_count_in_group:
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
    requested_count = len(registers_dict)
    total_fetched_count = sum((group[-1].address + group[-1].quantity - group[0].address) for group in groups)
    junk_count = max(0, total_fetched_count - requested_count)
    junk_percentage = (junk_count / total_fetched_count * 100) if total_fetched_count > 0 else 0.0

    # Log register summary and efficiency metrics
    self._log.info(f"{self._register_type.name} registers fetch summary: "
                   f"{requested_count} requested, {total_fetched_count} total read, "
                   f"junk: {junk_count} ({junk_percentage:.0f}%)")

    return groups

  async def update_cache(self) -> None:
    # Acquire client lock for the entire polling sequence
    async with self._logger_client_lock:
      if not self._registers_cache:
        return

      # Purge cache items that have not been accessed for more than purge timeout
      self._purge_inactive_registers()

      if not self._registers_cache:
        return

      now = time.monotonic()
      cache_snapshot: Dict[int, DeyeRegisterCacheData] = {}

      for addr, data in self._registers_cache.items():
        # Skip virtual registers from remote inverter polling
        if self._virtual_provider.is_virtual_register(addr):
          continue

        # Keep entry only if caching time has expired
        if (now - data.read_ts) >= data.caching_time:
          cache_snapshot[addr] = data

      if not cache_snapshot:
        return

      # Output all expired addresses from cache snapshot at once
      expired_str = ", ".join(str(addr) for addr in sorted(cache_snapshot.keys()))
      self._log.info(f"Expired {self._register_type.name.lower()} registers: {expired_str}")

      groups = self._get_register_groups(cache_snapshot)

      for group in groups:
        start_address = group[0].address
        last_register = group[-1]
        block_end = last_register.address + last_register.quantity
        quantity_to_read = block_end - start_address

        addresses_str = ", ".join(str(addr) for addr in range(start_address, start_address + quantity_to_read))
        self._log.info(f"Update {self._register_type.name.lower()} registers from inverter: {addresses_str}")

        await asyncio.sleep(1)

        try:
          values = await self._fetch_registers_from_inverter(start_address, quantity_to_read)
        except Exception as e:
          self._log.error(f"Failed to read {self._register_type.name.lower()} group starting at {start_address}: {e}")
          continue

        now = time.monotonic()
        for i, value in enumerate(values):
          reg_address = start_address + i

          # Skip updating virtual registers with data from physical inverter
          if self._virtual_provider.is_virtual_register(reg_address):
            continue

          # Update only registers that are already present in the cache
          existing = self._registers_cache.get(reg_address)
          if existing is not None:
            self._registers_cache[reg_address] = DeyeRegisterCacheData(
              address = reg_address,
              quantity = 1,
              caching_time = self._caching_time_holder.get_caching_time(reg_address),
              read_ts = now,
              last_access_ts = existing.last_access_ts,
              values = [value],
            )

  def _purge_inactive_registers(self) -> None:
    now = time.monotonic()
    inactive_addresses = [
      addr for addr, item in self._registers_cache.items()
      if (now - item.last_access_ts) >= self._config.CACHE_PURGE_TIMEOUT
      and not self._virtual_provider.is_virtual_register(addr)
    ]

    if inactive_addresses:
      addresses_str = ", ".join(str(addr) for addr in sorted(inactive_addresses))
      self._log.info(f"Purge inactive {self._register_type.name.lower()} registers: {addresses_str}")

      for address in inactive_addresses:
        del self._registers_cache[address]

  async def get_or_fetch_registers(
    self,
    start_address: int,
    quantity: int,
    client_ip: str,
    client_port: int,
  ) -> List[int]:
    addresses_str = ", ".join(str(addr) for addr in range(start_address, start_address + quantity))
    self._log.info(f"{client_ip}:{client_port} Read {self._register_type.name.lower()} "
                   f"registers: {addresses_str}")

    # Update virtual registers locally before retrieving from cache
    self._update_virtual_registers(
      client_ip = client_ip,
      client_port = client_port,
    )

    missing = False

    # Check if any requested address is missing in cache
    for address in range(start_address, start_address + quantity):
      if address not in self._registers_cache:
        missing = True
        break

    # If cache miss occurred, fetch data immediately from inverter
    if missing:
      try:
        # Synchronize access to physical client across concurrent client calls
        async with self._logger_client_lock:
          missing = False

          # Double check if any requested address is missing in cache after acquiring the lock
          for address in range(start_address, start_address + quantity):
            if address not in self._registers_cache:
              missing = True
              break

          if missing:
            missing_str = ", ".join(str(addr) for addr in range(start_address, start_address + quantity))
            self._log.warning(f"{client_ip}:{client_port} Fetching missing {self._register_type.name.lower()} "
                              f"registers from inverter: {missing_str}")

            values = await self._fetch_registers_from_inverter(start_address, quantity)

            now = time.monotonic()
            for i, val in enumerate(values):
              reg_address = start_address + i

              # Skip updating virtual registers with data from physical inverter
              if self._virtual_provider.is_virtual_register(reg_address):
                continue

              existing = self._registers_cache.get(reg_address)
              last_access = existing.last_access_ts if existing else now
              self._registers_cache[reg_address] = DeyeRegisterCacheData(
                address = reg_address,
                quantity = 1,
                caching_time = self._caching_time_holder.get_caching_time(reg_address),
                read_ts = now,
                last_access_ts = last_access,
                values = [val],
              )

      except Exception as e:
        self._log.error(f"Failed to fetch missing {self._register_type.name.lower()} "
                        f"registers starting at {start_address}: {e}")

    # Retrieve values from cache and recreate object with updated last access timestamp
    values: List[int] = []

    now = time.monotonic()
    for address in range(start_address, start_address + quantity):
      cached_item = self._registers_cache.get(address)
      if cached_item:
        self._registers_cache[address] = DeyeRegisterCacheData(
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

  async def _fetch_registers_from_inverter(self, start_address: int, quantity: int) -> List[int]:
    await self._logger_client.connect()
    try:
      if self._register_type == DeyeRegisterType.Holding:
        return await self._logger_client.read_holding_registers(start_address, quantity)
      elif self._register_type == DeyeRegisterType.Input:
        return await self._logger_client.read_input_registers(start_address, quantity)
      else:
        raise ValueError(f"Unsupported register type: {self._register_type}")
    finally:
      try:
        await self._logger_client.disconnect()
      except Exception as e:
        self._log.error(f"Error disconnecting from logger after fetching {self._register_type.name.lower()} "
                        f"registers starting at {start_address}: {e}")
