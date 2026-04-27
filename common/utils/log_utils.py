import sys
import logging

from hourly_overwrite_file_handler import HourlyOverwriteFileHandler

class LogUtils:
  @staticmethod
  def setup_hourly_overwrite_file_logger(
    log_dir: str,
    log_file_template: str,
    log_level: int = logging.INFO,
    name: str = "",
    clear_handlers = True,
    log_to_console = True,
  ) -> logging.Logger:
    logger = logging.getLogger(name)

    # Clear existing handlers to prevent duplicate logs
    if clear_handlers and logger.hasHandlers():
      logger.handlers.clear()

    logger.setLevel(log_level)

    formatter = logging.Formatter(
      "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
      "%Y-%m-%d %H:%M:%S",
    )

    file_handler = HourlyOverwriteFileHandler(
      directory = log_dir,
      log_file_template = log_file_template,
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if log_to_console:
      console = logging.StreamHandler(sys.stdout)
      console.setFormatter(formatter)
      logger.addHandler(console)

    return logger
