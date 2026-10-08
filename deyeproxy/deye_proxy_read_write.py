"""
Deye TCP Proxy Server

Author: Dmitry Smirnov 
https://github.com/smirnovhub

This module provides a thread-safe, exclusive-access proxy for communicating with 
Solarman V5 data loggers (found in Deye, Sunsynk, and other inverters). 

The proxy solves the "single-connection" limitation of the hardware by queuing 
multiple client requests and ensuring only one session is active at a time 
using a global threading lock.

Architecture:
    - Main thread listens for incoming TCP connections (e.g., from Home Assistant).
    - Each client is handled in a separate 'ProxyMainThread'.
    - A global 'logger_lock' ensures serialized access to the physical logger.
    - Bi-directional data transfer is managed by two dedicated full-duplex threads.
    - Strict timeouts and 'half-close' (TCP shutdown) patterns are used to 
      ensure the logger is released promptly.

Usage:
    Run the script with the required environment variables.
    The proxy will listen on 0.0.0.0:8899 by default.

    Example:
        $ LOGGER_HOST=1.2.3.4 python3 deyeproxy.py
"""
import os
import sys
import time
import errno
import logging
import socket
import signal
import threading

from typing import Tuple, Optional

utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../common/utils"))
sys.path.append(utils_path)

from log_utils import LogUtils
from common_utils import CommonUtils
from src.deye_proxy_config import DeyeProxyConfig

class SolarmanReadWriteProxy:
  def __init__(
    self,
    config: DeyeProxyConfig,
  ):
    self._config = config

    self._logger = LogUtils.setup_hourly_overwrite_file_logger(
      name = "deye-proxy-main",
      log_dir = f"data/{self._config.LOG_NAME}",
      log_file_template = "deye-proxy-{0}.log",
    )

    self._logger_wait = LogUtils.setup_hourly_overwrite_file_logger(
      name = "deye-proxy-wait",
      log_dir = f"data/{self._config.LOG_NAME}",
      log_file_template = "deye-proxy-wait-{0}.log",
      clear_handlers = False,
    )

    # Global lock to synchronize access to the physical logger
    self._logger_lock: threading.Lock = threading.Lock()

    # Stop flag: A thread-safe way to manage the program's lifecycle
    self._shutdown_event = threading.Event()

    self._log_level = logging.INFO
    if self._config.LOG_LEVEL in logging._nameToLevel:
      self._log_level = logging._nameToLevel[self._config.LOG_LEVEL]

  def _forward_data(
    self,
    source: socket.socket,
    destination: socket.socket,
    source_timeout: float,
    stop_event: threading.Event,
    direction: str,
  ) -> None:
    """
    Bi-directional data forwarding with specific timeout for the source socket.
    """
    total_bytes = 0
    # Set the specific timeout for this direction
    source.settimeout(source_timeout)

    try:
      while not stop_event.is_set():
        try:
          data = source.recv(1024)
          if not data:
            # Remote end closed connection
            try:
              destination.shutdown(socket.SHUT_WR)
            except Exception:
              pass
            break

          destination.sendall(data)
          total_bytes += len(data)
        except socket.timeout:
          # This is where the specific timeout hits
          self._logger.error(f"{direction} timed out after {source_timeout}s of inactivity")
          break
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
          self._logger.error(f"{direction} connection reset by peer")
          break
    except Exception as e:
      self._logger.debug(f"{direction} exception: {e}")
    finally:
      # Signals the other thread and main loop to stop
      stop_event.set()
      self._logger.info(f"{direction} bytes sent: {total_bytes}")

  def _handle_client(self, client_sock: socket.socket, client_ip: str, client_port: int) -> None:
    """
    Manages a single client session and enforces exclusive access to the logger.
    """
    if self._shutdown_event.is_set():
      client_sock.close()
      return

    start_wait = time.time()
    self._logger.info(f"{client_ip}:{client_port} Client wants connect "
                      f"to {self._config.LOGGER_HOST}:{self._config.LOGGER_PORT}...")

    acquired = self._logger_lock.acquire(timeout = self._config.CLIENT_WAIT_TIMEOUT)

    if not acquired:
      self._logger.error(f"{client_ip}:{client_port} Could not acquire lock within "
                         f"{self._config.CLIENT_WAIT_TIMEOUT}s. Connection rejected.")
      client_sock.close()
      return

    try:
      session_start = time.time()
      wait_duration = session_start - start_wait

      if self._shutdown_event.is_set():
        client_sock.close()
        return

      logger_sock: Optional[socket.socket] = None

      self._logger.info(f"{client_ip}:{client_port} Lock acquired "
                        f"(waited {wait_duration:.2f}s). Connecting to logger...")

      if wait_duration > 0.1:
        self._logger_wait.warning(f"{client_ip}:{client_port} Wait duration: {wait_duration:.2f}s")

      # Open connection to the real hardware
      logger_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      logger_sock.settimeout(self._config.CONNECT_TIMEOUT)
      logger_sock.connect((self._config.LOGGER_HOST, self._config.LOGGER_PORT))

      logger_ip, logger_port = logger_sock.getpeername()

      self._logger.info(f"{client_ip}:{client_port} Bridge established: "
                        f"{client_ip}:{client_port} <-> {logger_ip}:{logger_port}")

      stop_event = threading.Event()

      # Start forwarding threads
      # Using threads to handle full-duplex communication
      c2l = threading.Thread(
        target = self._forward_data,
        daemon = True,
        args = (
          client_sock,
          logger_sock,
          self._config.CLIENT_IDLE_TIMEOUT,
          stop_event,
          f"{client_ip}:{client_port} Client -> Logger",
        ),
        name = "ClientToLoggerThread",
      )

      l2c = threading.Thread(
        target = self._forward_data,
        daemon = True,
        args = (
          logger_sock,
          client_sock,
          self._config.LOGGER_IDLE_TIMEOUT,
          stop_event,
          f"{client_ip}:{client_port} Logger -> Client",
        ),
        name = "LoggerToClientThread",
      )

      c2l.start()
      l2c.start()

      wait_interval = 1.0
      elapsed_time = 0.0

      while not stop_event.is_set() and not self._shutdown_event.is_set():
        if stop_event.wait(timeout = wait_interval):
          break

        elapsed_time += wait_interval
        if elapsed_time >= self._config.SESSION_TIMEOUT:
          self._logger.error(f"{client_ip}:{client_port} Session timed out after {self._config.SESSION_TIMEOUT}s")

          stop_event.set()

          try:
            if logger_sock:
              logger_sock.shutdown(socket.SHUT_RDWR)
          except Exception:
            pass

          try:
            client_sock.shutdown(socket.SHUT_RDWR)
          except Exception:
            pass

          c2l.join(timeout = 1.5)
          l2c.join(timeout = 1.5)

          break

      stop_event.set()

    except socket.timeout:
      self._logger.error(f"{client_ip}:{client_port} Connection to logger timed out")
    except ConnectionRefusedError:
      self._logger.error(f"{client_ip}:{client_port} Logger refused connection")
    except OSError as e:
      if e.errno == errno.EHOSTUNREACH:
        self._logger.error(f"{client_ip}:{client_port} No route to host")
      else:
        self._logger.error(f"{client_ip}:{client_port} Unexpected error: {type(e).__name__}: {e}")
    except Exception as ee:
      self._logger.error(f"{client_ip}:{client_port} Unexpected error: {type(ee).__name__}: {ee}")
    finally:
      try:
        # Cleanup: ensure both sockets are closed and lock is released
        if logger_sock:
          logger_sock.close()

        client_sock.close()

        time.sleep(0.015)

        session_duration = time.time() - session_start + wait_duration
        self._logger.info(f"{client_ip}:{client_port} Session finished "
                          f"(duration {session_duration:.2f}s). Lock released")
        self._logger.info('-----------------------------------------------------------------------')
      except Exception as e:
        self._logger.error(str(e))
      finally:
        self._logger_lock.release()

  def _handle_exit(self, sig, frame) -> None:
    """
    Signal handler function.
    Triggered when Docker sends SIGTERM or when you press Ctrl+C (SIGINT).
    """
    self._logger.info(f"Received signal {sig}. Shutting down gracefully...")
    # This wakes up the .wait() method in the loop below immediately
    self._shutdown_event.set()

  def run(self) -> None:
    # Register the handlers for termination signals
    # SIGTERM is sent by 'docker stop'
    signal.signal(signal.SIGTERM, self._handle_exit)
    # SIGINT is sent by Ctrl+C
    signal.signal(signal.SIGINT, self._handle_exit)

    server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
      # Allow immediate reuse of the port after restart
      server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception as e:
      self._logger.error(f"Failed to call setsockopt: {e}")

    try:
      server.bind((self._config.PROXY_HOST, self._config.PROXY_PORT))
    except Exception as e:
      self._logger.error(f"Failed to bind port {self._config.PROXY_PORT} on {self._config.PROXY_HOST}: {e}")
      server.close()
      sys.exit(1)

    try:
      server.listen(self._config.MAX_CONCURRENT_CONNECTIONS)
    except Exception as e:
      self._logger.error(f"Failed to listen on port {self._config.PROXY_PORT}: {e}")
      server.close()
      sys.exit(1)

    external_ip = CommonUtils.get_external_ip(self._config.LOGGER_HOST, self._config.LOGGER_PORT)
    actual_ip = external_ip if external_ip else self._config.PROXY_HOST

    log_level_name = logging._levelToName[self._log_level]

    self._logger.info(f"------- Deye Read-Write Proxy started -------")
    self._logger.info(f"Target logger       : {self._config.LOGGER_HOST}:{self._config.LOGGER_PORT}")
    self._logger.info(f"Listening on        : {actual_ip}:{self._config.PROXY_PORT}")
    self._logger.info(f"Max connections     : {self._config.MAX_CONCURRENT_CONNECTIONS}")
    self._logger.info(f"Client wait timeout : {self._config.CLIENT_WAIT_TIMEOUT}s")
    self._logger.info(f"Connect timeout     : {self._config.CONNECT_TIMEOUT:g}s")
    self._logger.info(f"Client idle timeout : {self._config.CLIENT_IDLE_TIMEOUT:g}s")
    self._logger.info(f"Logger idle timeout : {self._config.LOGGER_IDLE_TIMEOUT:g}s")
    self._logger.info(f"Session timeout     : {self._config.SESSION_TIMEOUT:g}s")
    self._logger.info(f"Read only           : {self._config.READ_ONLY}")
    self._logger.info(f"Log level           : {log_level_name}")
    self._logger.info(f"----------------------------------")

    server.settimeout(1.0)

    try:
      while not self._shutdown_event.is_set():
        try:
          # Accept returns a tuple of (socket object, address info)
          client_info: Tuple[socket.socket, Tuple[str, int]] = server.accept()
          client_sock, client_addr = client_info
          client_ip, client_port = client_addr

          # Spawn a thread for each client
          thread = threading.Thread(
            target = self._handle_client,
            daemon = True,
            args = (client_sock, client_ip, client_port),
            name = "ProxyMainThread",
          )

          thread.start()
        except socket.timeout:
          continue
        except Exception as e:
          self._logger.error(f"Accept error: {e}")
          time.sleep(1)
    finally:
      server.close()
      self._logger.info("Server socket closed.")

      for handler in logging.getLogger().handlers:
        handler.flush()

      sys.stdout.flush()
      sys.stderr.flush()
