import os
import sys
import json
import traceback

from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from deye_web_dependency_provider import DeyeWebDependencyProvider

#import logging
#from deye_utils import DeyeUtils

#logging.basicConfig(
#  filename = '/tmp/deyeweb.log',
#  filemode = 'w',
#  level = logging.INFO,
#  format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
#  datefmt = DeyeUtils.time_format_str,
#)

dependency_provider = DeyeWebDependencyProvider()

def send_error_and_exit(message: str, callstack: str = '') -> None:
  constants = dependency_provider.constants
  if constants is None:
    result = {
      "error": f"Error: {message} (constants module not available)",
    }
  else:
    result = {
      constants.result_error_field: f'Error: {message}',
    }

    if callstack and constants.print_call_stack_on_exception:
      result[constants.result_callstack_field] = f'<pre>{callstack}</pre>'

  print(json.dumps(result))
  sys.exit(1)

dependency_provider = DeyeWebDependencyProvider()

try:
  # Read json from php
  raw = sys.stdin.read()

  if not raw:
    send_error_and_exit('JSON request is empty')

  json_data = json.loads(raw)

  # Lazy load back params processor
  params_processor = dependency_provider.back_params_processor
  if params_processor is None:
    all_errors = dependency_provider.get_all_errors()
    error_text = "\n".join(f"{name}: {err}" for name, err in all_errors.items())
    send_error_and_exit(f"Params processor module not available: {error_text}")
  result = params_processor.get_params(json_data)
except Exception as e:
  known_exception_class = dependency_provider.known_exception
  utils_class = dependency_provider.utils

  # Handle known exception safely (without crashing if class not loaded)
  if known_exception_class and isinstance(known_exception_class, type) and isinstance(
      e, known_exception_class) and utils_class:
    exception_str = utils_class.get_tail(str(e).strip('"'), ':')
    send_error_and_exit(exception_str, traceback.format_exc())
  else:
    send_error_and_exit(str(e), traceback.format_exc())

# Convert result to JSON string
json_str = json.dumps(result)

#with open("/tmp/back.json", "w", encoding = "utf-8") as f:
#  f.write(json.dumps(result, indent = 2, ensure_ascii = False))

#from deye_web_utils import DeyeWebUtils
#with open("/tmp/back_classes.txt", "w", encoding = "utf-8") as f:
#  f.write(DeyeWebUtils.get_deye_class_objects_count())

# Return json to php
print(json_str)
