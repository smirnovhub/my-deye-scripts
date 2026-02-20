import os
import sys

from pathlib import Path

current_path = Path(__file__).parent.resolve()
modules_path = (current_path / '../modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, ['src', '../deye/src', '../common'])

from deye_web_front_content_builder import DeyeWebFrontContentBuilder

front_content_builder = DeyeWebFrontContentBuilder()
content = front_content_builder.get_front_html()

print(content)

#from deye_web_utils import DeyeWebUtils
#with open("/tmp/front_classes_count.txt", "w", encoding = "utf-8") as f:
#  f.write(DeyeWebUtils.get_deye_class_objects_count())
