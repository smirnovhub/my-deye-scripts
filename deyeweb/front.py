import os
import sys
import logging
import traceback

from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from env_utils import EnvUtils
from deye_web_dependency_provider import DeyeWebDependencyProvider
from hourly_overwrite_file_handler import HourlyOverwriteFileHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
  "[%(asctime)s.%(msecs)03d] %(message)s",
  "%Y-%m-%d %H:%M:%S",
)

log_name = EnvUtils.get_log_name("deyeweb")
data_dir = f"data/{log_name}"

file_handler = HourlyOverwriteFileHandler(
  directory = data_dir,
  log_file_template = f"deyeweb-front-{{0}}.log",
)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

dependency_provider = DeyeWebDependencyProvider()

builder = dependency_provider.front_builder

builder = dependency_provider.front_builder
if builder:
  try:
    html = builder.get_front_html()
    print(html)
  except Exception as e:
    logger.error(traceback.format_exc())
    print(f"<h1>Frontend Error</h1><pre>{str(e)}\n{traceback.format_exc()}</pre>")
else:
  # Get all errors as a formatted string
  all_errors = dependency_provider.get_all_errors()
  error_text = "\n".join(f"{name}: {err}" for name, err in all_errors.items())
  logger.error(error_text)
  print(f"<h1>Frontend Error</h1><pre>{error_text}</pre>")

for handler in logging.getLogger().handlers:
  handler.flush()

sys.stdout.flush()
sys.stderr.flush()

#from deye_web_utils import DeyeWebUtils
#with open("/tmp/front_classes_count.txt", "w", encoding = "utf-8") as f:
#  f.write(DeyeWebUtils.get_deye_class_objects_count())
