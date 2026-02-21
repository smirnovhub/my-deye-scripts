import os
import sys
import traceback

from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from deye_web_dependency_provider import DeyeWebDependencyProvider

dependency_provider = DeyeWebDependencyProvider()

builder = dependency_provider.front_builder

builder = dependency_provider.front_builder
if builder is not None:
  try:
    html = builder.get_front_html()
    print(html)
  except Exception as e:
    print(f"<h1>Frontend Error</h1><pre>{str(e)}\n{traceback.format_exc()}</pre>")
else:
  # Get all errors as a formatted string
  all_errors = dependency_provider.get_all_errors()
  error_text = "\n".join(f"{name}: {err}" for name, err in all_errors.items())
  print(f"<h1>Frontend Error</h1><pre>{error_text}</pre>")

#from deye_web_utils import DeyeWebUtils
#with open("/tmp/front_classes_count.txt", "w", encoding = "utf-8") as f:
#  f.write(DeyeWebUtils.get_deye_class_objects_count())
