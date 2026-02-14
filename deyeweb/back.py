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

from deye_web_utils import DeyeWebUtils
from deye_web_constants import DeyeWebConstants
from deye_web_params_processor import DeyeWebParamsProcessor
from deye_exceptions import DeyeKnownException

#import logging
#from deye_utils import DeyeUtils

#logging.basicConfig(
#  filename = '/tmp/deyeweb.log',
#  filemode = 'w',
#  level = logging.INFO,
#  format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
#  datefmt = DeyeUtils.time_format_str,
#)

def send_error_and_exit(message: str, callstack: str = '') -> None:
  result = {
    DeyeWebConstants.result_error_field: f'Error: {message}',
  }

  if callstack and DeyeWebConstants.print_call_stack_on_exception:
    result[DeyeWebConstants.result_callstack_field] = f'<pre>{callstack}</pre>'

  print(json.dumps(result))
  sys.exit(1)

try:
  # Read json from php
  raw = sys.stdin.read()

  if not raw:
    send_error_and_exit('JSON request is empty')

  json_data = json.loads(raw)

  processor = DeyeWebParamsProcessor()
  result = processor.get_params(json_data)
except DeyeKnownException as e:
  exception_str = DeyeWebUtils.get_tail(str(e).strip('"'), ':')
  send_error_and_exit(exception_str, traceback.format_exc())
except Exception as ee:
  send_error_and_exit(str(ee), traceback.format_exc())

# Convert result to JSON string
json_str = json.dumps(result)

#with open("/tmp/back.json", "w", encoding = "utf-8") as f:
#  f.write(json.dumps(result, indent = 2, ensure_ascii = False))

#from deye_web_utils import DeyeWebUtils
#with open("/tmp/back_classes.txt", "w", encoding = "utf-8") as f:
#  f.write(DeyeWebUtils.get_deye_class_objects_count())

# Return json to php
print(json_str)
