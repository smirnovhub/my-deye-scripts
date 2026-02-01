"""
Solarman V5 TCP Proxy Server

This module provides a thread-safe, exclusive-access proxy for communicating with 
Solarman V5 data loggers (found in Deye, Sunsynk, and Victron inverters). 

The proxy solves the "single-connection" limitation of the hardware by queuing 
multiple client requests and ensuring only one session is active at a time 
using a global threading lock.

Architecture:
    1.  Main thread listens for incoming TCP connections (e.g., from Home Assistant).
    2.  Each client is handled in a separate 'ProxyMainThread'.
    3.  A global 'logger_lock' ensures serialized access to the physical logger.
    4.  Bi-directional data transfer is managed by two dedicated full-duplex threads.
    5.  Strict timeouts and 'half-close' (TCP shutdown) patterns are used to 
        ensure the logger is released promptly.

Usage:
    Run the script with the required environment variables.
    The proxy will listen on 0.0.0.0:8899 by default.

    Example:
        $ LOGGER_HOST=1.2.3.4 python3 deyeproxy.py
"""
import sys
import time
import logging
import socket
import signal
import threading

from typing import Tuple, Optional
from src.deyeproxy_config import DeyeProxyConfig

config = DeyeProxyConfig()
config.validate_or_exit()

# Global lock to synchronize access to the physical logger
logger_lock: threading.Lock = threading.Lock()

# Stop flag: A thread-safe way to manage the program's lifecycle
shutdown_event = threading.Event()

logging.basicConfig(
  level = logging.INFO,
  format = '%(asctime)s [%(levelname)s] %(message)s',
  datefmt = '%Y-%m-%d %H:%M:%S',
  handlers = [logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("deyeproxy")

def get_proxy_external_ip(host: Optional[str], port: int) -> Optional[str]:
  if not host:
    return None

  try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.connect((host, port))
      return s.getsockname()[0]
  except Exception:
    return None

def forward_data(
  source: socket.socket,
  destination: socket.socket,
  stop_event: threading.Event,
) -> None:
  """
  Bi-directional data forwarding between two sockets.
  """
  try:
    while not stop_event.is_set():
      data = source.recv(1024)
      if not data:
        try:
          destination.shutdown(socket.SHUT_WR)
        except Exception:
          pass
        break
      destination.sendall(data)
  except Exception:
    pass
  finally:
    stop_event.set()

def handle_client(client_sock: socket.socket, client_ip: str, client_port: int) -> None:
  """
  Manages a single client session and enforces exclusive access to the logger.
  """
  if shutdown_event.is_set():
    client_sock.close()
    return

  start_wait = time.time()
  logger.info(f"Client {client_ip}:{client_port} is waiting for the lock...")

  with logger_lock:
    if shutdown_event.is_set():
      client_sock.close()
      return

    logger_sock: Optional[socket.socket] = None
    wait_duration = time.time() - start_wait
    session_start = time.time()

    logger.info(f"Lock acquired for {client_ip}:{client_port} "
                f"(waited {wait_duration:.2f}s). Connecting to logger...")

    try:
      # Open connection to the real hardware
      logger_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      logger_sock.settimeout(config.CONNECT_TIMEOUT)
      logger_sock.connect((config.LOGGER_HOST, config.LOGGER_PORT))

      # Set operational timeouts for data phase
      logger_sock.settimeout(config.DATA_TIMEOUT)
      client_sock.settimeout(config.DATA_TIMEOUT)

      logger.info(f"Bridge established: {client_ip}:{client_port} <-> {config.LOGGER_HOST}:{config.LOGGER_PORT}")

      stop_event = threading.Event()

      # Start forwarding threads
      # Using threads to handle full-duplex communication
      c2l = threading.Thread(
        target = forward_data,
        daemon = True,
        args = (client_sock, logger_sock, stop_event),
        name = "ClientToLoggerThread",
      )

      l2c = threading.Thread(
        target = forward_data,
        daemon = True,
        args = (logger_sock, client_sock, stop_event),
        name = "LoggerToClientThread",
      )

      c2l.start()
      l2c.start()

      wait_interval = 1.0
      elapsed_time = 0

      while not stop_event.is_set() and not shutdown_event.is_set():
        if stop_event.wait(timeout = wait_interval):
          break

        elapsed_time += wait_interval
        if elapsed_time >= config.DATA_TIMEOUT:
          logger.warning(f"Session timed out after {config.DATA_TIMEOUT}s for {client_ip}:{client_port}")
          break

      stop_event.set()

    except socket.timeout:
      logger.error(f"Connection to logger {config.LOGGER_HOST} timed out.")
    except ConnectionRefusedError:
      logger.error(f"Logger {config.LOGGER_HOST} refused connection.")
    except Exception as e:
      logger.error(f"Unexpected error: {type(e).__name__}: {e}")
    finally:
      # Cleanup: ensure both sockets are closed and lock is released
      if logger_sock:
        logger_sock.close()
      client_sock.close()

      session_duration = time.time() - session_start
      logger.info(f"Session finished (duration {session_duration:.2f}s). "
                  f"Lock released for {client_ip}:{client_port}.")
      logger.info('-----------------------------------------------------------------------')

def handle_exit(sig, frame):
  """
  Signal handler function.
  Triggered when Docker sends SIGTERM or when you press Ctrl+C (SIGINT).
  """
  logger.info(f"Received signal {sig}. Shutting down gracefully...")
  # This wakes up the .wait() method in the loop below immediately
  shutdown_event.set()

def main() -> None:
  # Register the handlers for termination signals
  # SIGTERM is sent by 'docker stop'
  signal.signal(signal.SIGTERM, handle_exit)
  # SIGINT is sent by Ctrl+C
  signal.signal(signal.SIGINT, handle_exit)

  server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:
    # Allow immediate reuse of the port after restart
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  except Exception as e:
    logger.error(f"Failed to call setsockopt: {e}")

  try:
    server.bind((config.PROXY_HOST, config.PROXY_PORT))
  except Exception as e:
    logger.error(f"Failed to bind port {config.PROXY_PORT}: {e}")
    server.close()
    sys.exit(1)

  try:
    server.listen(config.MAX_CONCURRENT_CONNECTIONS)
  except Exception as e:
    logger.error(f"Failed to listen on port {config.PROXY_PORT}: {e}")
    server.close()
    sys.exit(1)

  external_ip = get_proxy_external_ip(config.LOGGER_HOST, config.LOGGER_PORT)
  actual_ip = external_ip if external_ip else config.PROXY_HOST

  logger.info(f"--- Solarman V5 Proxy started ---")
  logger.info(f"Target logger   : {config.LOGGER_HOST}:{config.LOGGER_PORT}")
  logger.info(f"Listening on    : {actual_ip}:{config.PROXY_PORT}")
  logger.info(f"Max connections : {config.MAX_CONCURRENT_CONNECTIONS}")
  logger.info(f"Connect timeout : {config.CONNECT_TIMEOUT}s")
  logger.info(f"Data timeout    : {config.DATA_TIMEOUT}s")
  logger.info(f"---------------------------------")

  server.settimeout(1.0)

  try:
    while not shutdown_event.is_set():
      try:
        # Accept returns a tuple of (socket object, address info)
        client_info: Tuple[socket.socket, Tuple[str, int]] = server.accept()
        client_sock, client_addr = client_info
        client_ip, client_port = client_addr

        # Spawn a thread for each client
        thread = threading.Thread(
          target = handle_client,
          daemon = True,
          args = (client_sock, client_ip, client_port),
          name = "ProxyMainThread",
        )

        thread.start()
      except socket.timeout:
        continue
      except Exception as e:
        logger.error(f"Accept error: {e}")
        time.sleep(15)
  finally:
    server.close()
    logger.info("Server socket closed.")

if __name__ == "__main__":
  main()
