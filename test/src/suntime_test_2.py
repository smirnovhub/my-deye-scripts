import os
import re
import sys

from pathlib import Path
from datetime import datetime, timezone

base_path = '../..'
current_path = Path(__file__).parent.resolve()
modules_path = (current_path / base_path / 'modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(current_path, [])

from suntime import Sun, SunTimeException

def verify_suntime_calculations(file_path):
  with open(file_path, 'r', encoding = 'utf-8') as f:
    for line in f:
      line = line.strip()
      if not line:
        continue

      meta_match = re.search(r"(.*?)\s*Date:\s*([\d-]+)\s*\|\s*Lat:\s*([-\d.]+),\s*Lon:\s*([-\d.]+)", line)
      if not meta_match:
        continue

      number = meta_match.group(1)
      ref_date_str = meta_match.group(2)
      lat = float(meta_match.group(3))
      lon = float(meta_match.group(4))

      target_date = datetime.strptime(ref_date_str, "%Y-%m-%d").replace(tzinfo = timezone.utc)

      expected_exception = None
      expected_sunrise = None
      expected_sunset = None

      if "Exception:" in line:
        expected_exception = line.split("Exception:")[1].strip()
      else:
        time_match = re.search(r"Sunrise:\s*([\d-]+\s\d{2}:\d{2}:\d{2})\s*\|\s*" \
                               r"Sunset:\s*([\d-]+\s\d{2}:\d{2}:\d{2})", line)
        if time_match:
          expected_sunrise = time_match.group(1)
          expected_sunset = time_match.group(2)

      sun_calculator = Sun(lat, lon)

      try:
        sunrise_time = sun_calculator.get_sunrise_time(at_date = target_date)
        sunset_time = sun_calculator.get_sunset_time(at_date = target_date)

        actual_sunrise = sunrise_time.strftime("%Y-%m-%d %H:%M:%S")
        actual_sunset = sunset_time.strftime("%Y-%m-%d %H:%M:%S")

        if expected_exception:
          print(f"Mismatch at {number} Date: {ref_date_str}, Lat: {lat}, Lon: {lon}")
          print(f"Expected: Exception '{expected_exception}'")
          print(f"Actual:   Sunrise: {actual_sunrise}, Sunset: {actual_sunset}")
          sys.exit(1)

        if actual_sunrise != expected_sunrise or actual_sunset != expected_sunset:
          print(f"Mismatch at {number} Date: {ref_date_str}, Lat: {lat}, Lon: {lon}")
          print(f"Expected: Sunrise: {expected_sunrise} | Sunset: {expected_sunset}")
          print(f"Actual:   Sunrise: {actual_sunrise} | Sunset: {actual_sunset}")
          sys.exit(1)

      except SunTimeException as e:
        actual_exception = str(e)

        if not expected_exception:
          print(f"Mismatch at {number} Date: {ref_date_str}, Lat: {lat}, Lon: {lon}")
          print(f"Expected: Sunrise: {expected_sunrise} | Sunset: {expected_sunset}")
          print(f"Actual: Exception '{actual_exception}'")
          sys.exit(1)

        if actual_exception != expected_exception:
          print(f"Mismatch at {number} Date: {ref_date_str}, Lat: {lat}, Lon: {lon}")
          print(f"Expected Exception: '{expected_exception}'")
          print(f"Actual Exception: '{actual_exception}'")
          sys.exit(1)

  print("All suntime calculations match successfully.")

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(f"Usage: python {Path(sys.argv[0]).name} <path_to_text_file>")
    sys.exit(1)

  verify_suntime_calculations(sys.argv[1])
