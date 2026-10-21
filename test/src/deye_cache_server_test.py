import os
import sys
import logging
import asyncio
import time
import aiohttp
import unittest

from pathlib import Path
from typing import Any, Union

base_path = '../..'
current_path = Path(__file__).parent.resolve()
modules_path = (current_path / base_path / 'modules').resolve()

os.chdir(current_path)
sys.path.append(str(modules_path))

from common_modules import import_dirs

import_dirs(
  current_path,
  [
    os.path.join(base_path, 'common'),
    os.path.join(base_path, 'deye/src'),
    os.path.join(base_path, 'deyestorage'),
  ],
)

from deye_utils import DeyeUtils
from deye_test_utils import DeyeTestUtils
from deye_loggers import DeyeLoggers
from deye_storage_config import DeyeStorageConfig

# Configuration
BASE_URL = f"http://{DeyeTestUtils.storage_server_host}:{DeyeTestUtils.storage_server_port}"
CACHE_URL = f"{BASE_URL}/cache"
PING_URL = f"{BASE_URL}/ping"

log = logging.getLogger()

STRESS_REQUESTS = 1000

class TestDeyeCacheExtended(unittest.IsolatedAsyncioTestCase):
  session: aiohttp.ClientSession
  config: DeyeStorageConfig

  async def asyncSetUp(self):
    """
    Global cleanup and session initialization.
    """
    self.session = aiohttp.ClientSession()
    self.config = DeyeStorageConfig()
    try:
      async with self.session.delete(CACHE_URL) as response:
        if response.status not in (200, 404):
          log.warning(f"Unexpected status code during cache cleanup: {response.status}")
    except aiohttp.ClientConnectionError:
      log.error(f"Error: Server not found at {BASE_URL}")
      sys.exit(1)

  async def asyncTearDown(self):
    """
    Reset cache after each test and close the session properly.
    """
    try:
      async with self.session.delete(CACHE_URL):
        pass
    except Exception:
      pass
    await self.session.close()

  async def test_ping(self):
    """Test health check endpoint."""
    async with self.session.get(PING_URL) as response:
      self.assertEqual(response.status, 200)
      data = await response.json()
      self.assertEqual(data, {"status": "success"})

  async def test_complex_nested_merge(self):
    """
    Test deep merging with multi-level nested dictionaries.
    """
    key = "nested_dev"

    initial = {"settings": {"mode": "auto", "limits": {"max_temp": 60}}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = initial) as resp:
      self.assertEqual(resp.status, 200)

    update = {"settings": {"limits": {"min_temp": 10}, "active": True}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = update) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      self.assertEqual(res.status, 200)
      res_json = await res.json()

    self.assertEqual(res_json["settings"]["mode"], "auto")
    self.assertEqual(res_json["settings"]["limits"]["max_temp"], 60)
    self.assertEqual(res_json["settings"]["limits"]["min_temp"], 10)
    self.assertEqual(res_json["settings"]["active"], True)

  async def test_different_data_types(self):
    """
    Test that various JSON types (lists, strings, nulls) are handled correctly.
    """
    key = "types_dev"
    payload = {
      "str_val": "hello",
      "int_val": 100,
      "float_val": 99.9,
      "list_val": [1, 2, 3],
      "bool_val": False,
      "null_val": None
    }

    async with self.session.post(f"{CACHE_URL}/{key}", json = payload) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      self.assertEqual(res.status, 200)
      res_json = await res.json()

    for k, v in payload.items():
      self.assertEqual(res_json[k], v, f"Value mismatch for key: {k}")

  async def test_delete_specific_key(self):
    """Test DELETE /cache/{key} method."""
    key = "to_be_deleted"
    async with self.session.post(f"{CACHE_URL}/{key}", json = {"data": 1}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.delete(f"{CACHE_URL}/{key}") as del_res:
      self.assertEqual(del_res.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as resp:
      self.assertEqual(resp.status, 404)

  async def test_global_delete(self):
    """Test global cache reset (DELETE /cache)."""
    async with self.session.post(f"{CACHE_URL}/k1", json = {"v": 1}) as resp:
      self.assertEqual(resp.status, 200)
    async with self.session.post(f"{CACHE_URL}/k2", json = {"v": 2}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.delete(CACHE_URL) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.options(CACHE_URL) as stats:
      self.assertEqual(stats.status, 200)
      stats_json = await stats.json()

    self.assertEqual(stats_json["keys_used"], 0)
    self.assertEqual(stats_json["bytes_used"], 0)

  async def test_max_keys_limit(self):
    """
    Test that server returns 403 when trying to exceed MAX_KEYS_COUNT.
    """
    async with self.session.delete(CACHE_URL) as resp:
      self.assertEqual(resp.status, 200)

    limit = self.config.MAX_KEYS_COUNT
    for i in range(limit):
      async with self.session.post(f"{CACHE_URL}/dev_{i}", json = {"data": i}) as resp:
        self.assertEqual(resp.status, 200)

    async with self.session.post(f"{CACHE_URL}/overflow_key", json = {"data": "fail"}) as res:
      self.assertEqual(res.status, 403)
      res_json = await res.json()
      self.assertIn("Maximum number of keys exceeded", res_json["detail"])

  async def test_json_size_limit_per_reqeust(self):
    """
    Test that each json request cannot exceed MAX_JSON_SIZE.
    """
    key = "big_storage_dev"
    large_chunk = {"data": "x" * (self.config.MAX_JSON_SIZE - 150)}

    async with self.session.post(f"{CACHE_URL}/{key}", json = large_chunk) as resp:
      self.assertEqual(resp.status, 200)

    huge_update = {"extra": "y" * (self.config.MAX_JSON_SIZE + 10)}
    async with self.session.post(f"{CACHE_URL}/{key}", json = huge_update) as res:
      self.assertEqual(res.status, 413)
      res_json = await res.json()
      detail = res_json.get("detail", "")
      self.assertIn("JSON body size exceeded", detail)

  async def test_storage_size_limit_per_key_cumulative(self):
    """
    SECURITY: Test that the cumulative storage for a single key
    cannot exceed MAX_JSON_STORAGE_SIZE through multiple updates.
    """
    key = "cumulative_test_inverter"

    async with self.session.delete(CACHE_URL) as resp:
      self.assertEqual(resp.status, 200)

    chunk_size = self.config.MAX_JSON_SIZE - 100
    chunk_data = "x" * chunk_size

    num_requests_to_fill = (self.config.MAX_JSON_STORAGE_SIZE // chunk_size) + 2

    log.info(f"Filling storage for '{key}'")
    log.info(f"Chunk: {chunk_size}, Storage Limit: {self.config.MAX_JSON_STORAGE_SIZE}")

    for i in range(num_requests_to_fill):
      payload = {f"register_group_{i}": chunk_data}
      async with self.session.post(f"{CACHE_URL}/{key}", json = payload) as response:
        if i < num_requests_to_fill - 1:
          self.assertEqual(response.status, 200, f"Batch {i} failed prematurely with status {response.status}")
        else:
          self.assertEqual(response.status, 413, "Server failed to block cumulative storage overflow")
          res_json = await response.json()
          detail = res_json.get("detail", "")
          self.assertIn("JSON storage size exceeded", detail)

  async def test_concurrent_updates(self):
    """
    STRESS/RACE CONDITION TEST:
    Simulate multiple concurrent clients updating the same key.
    Verifies that asyncio.Lock on the server prevents data loss.
    """
    key = "race_condition_test"
    async with self.session.delete(f"{CACHE_URL}/{key}"):
      pass

    num_updates = 20
    updates = [{"update_id": i} for i in range(num_updates)]

    async def send_post(data):
      # Use the shared session pool instead of creating a new session
      async with self.session.post(f"{CACHE_URL}/{key}", json = data) as resp:
        return resp.status

    statuses = await asyncio.gather(*(send_post(data) for data in updates))

    for status in statuses:
      self.assertEqual(status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res_get:
      res = await res_get.json()
    for i in range(num_updates):
      self.assertIn("update_id", res)

  async def test_data_type_conflict_overwrite(self):
    """
    EDGE CASE:
    Verify behavior when a dictionary field is overwritten by a non-dictionary value.
    """
    key = "conflict_dev"

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"data": {"nested": 1}}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"data": 100}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      self.assertEqual(res.status, 200)
      res_json = await res.json()
      self.assertEqual(res_json["data"], 100)

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"data": {"new_nested": 2}}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res2:
      self.assertEqual(res2.status, 200)
      res_json2 = await res2.json()
      self.assertEqual(res_json2["data"]["new_nested"], 2)

  async def test_malformed_json_and_empty_payload(self):
    """
    SECURITY/ROBUSTNESS:
    Verify server behavior with empty bodies or invalid content types.
    """
    key = "malformed_test"

    async with self.session.post(f"{CACHE_URL}/{key}", headers = {"Content-Type": "application/json"}) as response:
      self.assertEqual(response.status, 422)

  async def test_deep_merge_array_handling(self):
    """
    LOGIC TEST:
    Verify how deep_merge handles lists (should overwrite, not extend).
    """
    key = "array_test"
    async with self.session.post(f"{CACHE_URL}/{key}", json = {"list": [1, 2]}) as resp:
      self.assertEqual(resp.status, 200)
    async with self.session.post(f"{CACHE_URL}/{key}", json = {"list": [3, 4]}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      self.assertEqual(res.status, 200)
      res_json = await res.json()
      self.assertEqual(res_json["list"], [3, 4])

  async def test_extreme_nesting_depth(self):
    """
    PERFORMANCE/STABILITY:
    Test very deep JSON nesting (20+ levels).
    """
    key = "extreme_nest"
    current: Any = "bottom"
    for i in range(20, 0, -1):
      current = {f"L{i}": current}

    async with self.session.post(f"{CACHE_URL}/{key}", json = current) as response:
      self.assertEqual(response.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      val = await res.json()
      for i in range(1, 21):
        val = val[f"L{i}"]
      self.assertEqual(val, "bottom")

  async def test_type_swapping_in_nesting(self):
    """
    ROBUSTNESS:
    Tests what happens when a deep nested dict is suddenly replaced by a primitive.
    """
    key = "swap_test"

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"a": {"b": {"c": 1}}}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"a": {"b": "string_value"}}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      res_json = await res.json()
      self.assertEqual(res_json["a"]["b"], "string_value")

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"a": {"b": {"new_dict": True}}}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      res_json = await res.json()
      self.assertIsInstance(res_json["a"]["b"], dict)
      self.assertTrue(res_json["a"]["b"]["new_dict"])

  async def test_large_number_of_keys_rapidly(self):
    """
    STRESS:
    Rapidly create many keys and then perform a global reset.
    """
    for i in range(self.config.MAX_KEYS_COUNT + 15):
      async with self.session.post(f"{CACHE_URL}/stress_{i}", json = {"data": i}):
        pass

    async with self.session.options(CACHE_URL) as stat_res_obj:
      stat_res = await stat_res_obj.json()
      self.assertEqual(stat_res["keys_used"], self.config.MAX_KEYS_COUNT)
      self.assertGreater(stat_res["bytes_used"], 0)

    async with self.session.delete(CACHE_URL) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.options(CACHE_URL) as stat_after_obj:
      stat_after = await stat_after_obj.json()
      self.assertEqual(stat_after["keys_used"], 0)
      self.assertEqual(stat_after["bytes_used"], 0)

  async def test_invalid_endpoints(self):
    """
    ROBUSTNESS:
    Test requests to non-existent paths.
    """
    async with self.session.get(f"{BASE_URL}/invalid/path/to/resource") as resp:
      self.assertEqual(resp.status, 404)

    async with self.session.get(f"{BASE_URL}/caches") as resp:
      self.assertEqual(resp.status, 404)

  async def test_invalid_http_methods(self):
    """
    ROBUSTNESS:
    Test using wrong HTTP methods for valid endpoints.
    """
    async with self.session.post(PING_URL) as resp:
      self.assertEqual(resp.status, 405)

    async with self.session.get(CACHE_URL) as resp:
      self.assertEqual(resp.status, 405)

    async with self.session.put(f"{CACHE_URL}/some_key", json = {"a": 1}) as resp:
      self.assertEqual(resp.status, 405)

  async def test_url_encoding_and_special_chars(self):
    """
    EDGE CASE:
    Test keys with special characters and URL encoding.
    """
    special_key = "key with $symbols"
    payload = {"data": "test"}

    async with self.session.post(f"{CACHE_URL}/{special_key}", json = payload) as resp_post:
      self.assertEqual(resp_post.status, 200)

    async with self.session.get(f"{CACHE_URL}/{special_key}") as resp_get:
      self.assertEqual(resp_get.status, 200)
      data = await resp_get.json()
      self.assertEqual(data["data"], "test")

  async def test_malformed_url_traversal(self):
    """
    SECURITY:
    Test for directory traversal attempts in the URL key.
    """
    key = "../root_key"
    async with self.session.post(f"{CACHE_URL}/{key}", json = {"hack": "attempt"}) as resp:
      self.assertEqual(resp.status, 404)

  async def test_docs_and_openapi_exposure(self):
    """
    SECURITY:
    Check if FastAPI default documentation is enabled.
    """
    for path in ["/docs", "/redoc", "/openapi.json"]:
      async with self.session.get(f"{BASE_URL}{path}") as resp:
        status = "ENABLED" if resp.status == 200 else "DISABLED"
        log.info(f"FastAPI auto-doc {path} is {status}")

  async def test_case_sensitivity(self):
    """
    EDGE CASE:
    Verify if paths are case-sensitive.
    """
    key = "case_test"
    async with self.session.post(f"{CACHE_URL}/{key}", json = {"v": 1}) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{BASE_URL}/CACHE/{key}") as resp:
      self.assertEqual(resp.status, 404)

    async with self.session.get(f"{BASE_URL}/PING") as resp:
      self.assertEqual(resp.status, 404)

  async def test_path_parameter_abuse(self):
    """
    SECURITY:
    Test sending forbidden characters or path segments within the key parameter.
    """
    key_with_slash = "inverter/01"
    async with self.session.get(f"{CACHE_URL}/{key_with_slash}") as resp:
      self.assertEqual(resp.status, 404)

  async def test_trailing_slashes(self):
    """
    ROBUSTNESS:
    Check behavior with trailing slashes.
    """
    async with self.session.get(f"{PING_URL}/") as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/somekey/") as resp:
      self.assertEqual(resp.status, 404)

  async def test_proxy_headers_spoofing(self):
    """
    SECURITY:
    Test how the server handles typical proxy headers.
    """
    key = "proxy_test"

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"data": 1}) as resp:
      self.assertEqual(resp.status, 200)
    async with self.session.get(f"{CACHE_URL}/{key}") as resp:
      res_no_proxy = await resp.json()

    ip = res_no_proxy.get("last_update_by")

    headers = {"X-Forwarded-For": "8.8.8.8"}
    async with self.session.post(f"{CACHE_URL}/{key}", json = {"data": 1}, headers = headers):
      pass

    async with self.session.get(f"{CACHE_URL}/{key}") as resp:
      res_with_proxy = await resp.json()
      self.assertEqual(res_with_proxy.get("last_update_by"), ip)

  async def test_deep_null_merging_logic(self):
    """
    LOGIC/STABILITY:
    Verify how the server handles 'null' during a deep merge.
    """
    key = "null_logic_test"

    initial = {"status": "online", "metrics": {"power": 5000, "temp": 45}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = initial) as resp:
      self.assertEqual(resp.status, 200)

    update = {"metrics": {"power": 6000, "temp": None}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = update) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      self.assertEqual(res.status, 200)
      res_json = await res.json()

    self.assertEqual(res_json["metrics"]["power"], 6000)
    self.assertIsNone(res_json["metrics"]["temp"])
    self.assertEqual(res_json["status"], "online")

    killer_update = {"metrics": {"temp": {"sub_temp": 20}}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = killer_update) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      final_res = await res.json()
      self.assertEqual(final_res["metrics"]["temp"]["sub_temp"], 20)

  async def test_stale_data_ignored_by_timestamp(self):
    """
    LOGIC TEST:
    Verify that incoming data is ignored if its 'ts_label' is older than or equal to cached.
    """
    key = "timestamp_test_dev"

    initial_payload = {"data": {"value": 100, "ts_label": 1700000000}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = initial_payload) as resp:
      self.assertEqual(resp.status, 200)

    stale_payload = {"data": {"value": 50, "ts_label": 1600000000}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = stale_payload) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res_obj:
      res = await res_obj.json()
      self.assertEqual(res["data"]["value"], 100)
      self.assertEqual(res["data"]["ts_label"], 1700000000)

    equal_payload = {"data": {"value": 200, "ts_label": 1700000000}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = equal_payload) as resp:
      self.assertEqual(resp.status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res_equal_obj:
      res_equal = await res_equal_obj.json()
      self.assertEqual(res_equal["data"]["value"], 100)

  async def test_mixed_timestamp_update(self):
    """
    LOGIC TEST:
    Verify that in a single request, only stale nested objects are ignored.
    """
    key = "mixed_ts_test"

    initial = {"sensor_a": {"val": 10, "ts_label": 1000}, "sensor_b": {"val": 20, "ts_label": 1000}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = initial):
      pass

    mixed_update = {"sensor_a": {"val": 15, "ts_label": 1100}, "sensor_b": {"val": 99, "ts_label": 900}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = mixed_update):
      pass

    async with self.session.get(f"{CACHE_URL}/{key}") as res_obj:
      res = await res_obj.json()
      self.assertEqual(res["sensor_a"]["val"], 15)
      self.assertEqual(res["sensor_b"]["val"], 20)

  async def test_timestamp_with_different_types(self):
    """
    EDGE CASE:
    Verify timestamp logic only triggers when both fields are numbers.
    """
    key = "ts_type_test"

    async with self.session.post(f"{CACHE_URL}/{key}", json = {"obj": {"val": 1, "ts_label": 100}}):
      pass

    update = {"obj": {"val": 2, "ts_label": "100"}}
    async with self.session.post(f"{CACHE_URL}/{key}", json = update):
      pass

    async with self.session.get(f"{CACHE_URL}/{key}") as res_obj:
      res = await res_obj.json()
      self.assertEqual(res["obj"]["val"], 2)
      self.assertEqual(res["obj"]["ts_label"], "100")

  async def test_update_and_get_average_int(self):
    """
    LOGIC TEST:
    Verify update_average calculation using path parameters.
    """
    key = "avg_path_test"

    c1, c2 = 10, 30
    endpoint1 = f"{BASE_URL}/average/{key}/{c1}/{c2}"
    async with self.session.post(endpoint1) as res1:
      self.assertEqual(res1.status, 200)
      data1 = await res1.json()
      self.assertEqual(data1["average"], c1 / (c1 + c2))
      self.assertEqual(data1["total"], c1 + c2)

    c3, c4 = 10, 10
    endpoint2 = f"{BASE_URL}/average/{key}/{c3}/{c4}"
    async with self.session.post(endpoint2) as res2:
      self.assertEqual(res2.status, 200)
      data2 = await res2.json()
      self.assertAlmostEqual(data2["average"], (c1 + c3) / (c1 + c2 + c3 + c4), places = 5)

    get_endpoint = f"{BASE_URL}/average/{key}"
    async with self.session.get(get_endpoint) as res_get:
      self.assertEqual(res_get.status, 200)
      data_get = await res_get.json()
      self.assertEqual(data_get["key"], key)
      self.assertEqual(data_get["count1"], c1 + c3)
      self.assertEqual(data_get["count2"], c2 + c4)

  async def test_update_average_small_floats(self):
    """
    LOGIC TEST: Small floats (1-10 range).
    """
    key = "avg_small_floats"
    c1, c2 = 1.25, 3.75

    endpoint = f"{BASE_URL}/average/{key}/{c1}/{c2}"
    async with self.session.post(endpoint) as res:
      self.assertEqual(res.status, 200)
      data = await res.json()
      self.assertEqual(data["average"], c1 / (c1 + c2))
      self.assertEqual(data["total"], c1 + c2)

  async def test_update_average_large_floats(self):
    """
    LOGIC TEST: Large floats (>100 range).
    """
    key = "avg_large_floats"
    c1, c2 = 120.5, 379.5

    endpoint = f"{BASE_URL}/average/{key}/{c1}/{c2}"
    async with self.session.post(endpoint) as res:
      self.assertEqual(res.status, 200)
      data = await res.json()
      self.assertEqual(data["average"], c1 / (c1 + c2))
      self.assertEqual(data["total"], c1 + c2)

  async def test_update_average_mixed_accumulation(self):
    """
    LOGIC TEST: Mixed ranges with accumulation.
    """
    key = "avg_mixed_accum"

    c1_small, c2_small = 1.1, 0.9
    async with self.session.post(f"{BASE_URL}/average/{key}/{c1_small}/{c2_small}"):
      pass

    c1_large, c2_large = 148.9, 249.1
    async with self.session.post(f"{BASE_URL}/average/{key}/{c1_large}/{c2_large}") as res:
      self.assertEqual(res.status, 200)
      data = await res.json()

    expected_c1 = c1_small + c1_large
    expected_c2 = c2_small + c2_large
    expected_total = expected_c1 + expected_c2
    expected_avg = expected_c1 / expected_total

    self.assertEqual(data["count1"], expected_c1)
    self.assertEqual(data["total"], expected_total)
    self.assertEqual(data["average"], expected_avg)

  async def test_average_with_float_artifact(self):
    """
    EDGE CASE: Verify handling of tiny float artifacts.
    """
    key = "artifact_test"
    c1 = 1.1
    c2 = 2.2

    endpoint = f"{BASE_URL}/average/{key}/{c1}/{c2}"
    async with self.session.post(endpoint) as res:
      self.assertEqual(res.status, 200)
      data = await res.json()

    def clean_num(v: float) -> Union[float, int]:
      v = round(v, 10)
      return int(v) if v.is_integer() else v

    expected_total = clean_num(c1 + c2)
    expected_avg = clean_num(c1 / expected_total)

    self.assertEqual(data["total"], expected_total)
    self.assertAlmostEqual(data["average"], expected_avg)

  async def test_average_with_sum_to_integer_artifact(self):
    """
    EDGE CASE: When sums slightly exceed an integer.
    """
    key = "sum_artifact_key"
    c1 = 100.00000000000001
    c2 = 0.00000000000002

    async with self.session.post(f"{BASE_URL}/average/{key}/{c1}/{c2}") as res:
      data = await res.json()
      self.assertTrue(float(data["total"]).is_integer())

  async def test_average_delete(self):
    """
    LOGIC TEST: Verify average entry removal.
    """
    key = "delete_test_key"
    async with self.session.post(f"{BASE_URL}/average/{key}/5/5"):
      pass

    async with self.session.delete(f"{BASE_URL}/average/{key}") as res_del:
      self.assertEqual(res_del.status, 200)

    async with self.session.get(f"{BASE_URL}/average/{key}") as res_get:
      self.assertEqual(res_get.status, 404)

  async def test_average_division_by_zero_path(self):
    """
    EDGE CASE: Verify zero values in path parameters.
    """
    key = "zero_path_test"
    async with self.session.post(f"{BASE_URL}/average/{key}/0/0") as res:
      self.assertEqual(res.status, 200)
      data = await res.json()
      self.assertEqual(data["average"], 0.0)

  async def test_massive_concurrent_stress_and_integrity(self):
    """
    STRESS/INTEGRITY TEST:
    Simulate massive concurrent async requests (1000 requests) updating a single key
    using the shared session pool.
    """
    key = "massive_stress_key"
    async with self.session.delete(f"{CACHE_URL}/{key}"):
      pass

    updates = [{f"field_{i}": i} for i in range(STRESS_REQUESTS)]

    async def send_post(data):
      # Use the shared session pool instead of creating a new session per request
      async with self.session.post(f"{CACHE_URL}/{key}", json = data) as resp:
        return resp.status

    statuses = await asyncio.gather(*(send_post(data) for data in updates))

    for status in statuses:
      self.assertEqual(status, 200)

    async with self.session.get(f"{CACHE_URL}/{key}") as res:
      self.assertEqual(res.status, 200)
      res_json = await res.json()
      for i in range(STRESS_REQUESTS):
        self.assertIn(f"field_{i}", res_json)
        self.assertEqual(res_json[f"field_{i}"], i)

  async def test_stress_concurrent_deep_merge_integrity(self):
    """
    STRESS / DATA INTEGRITY:

    Send thousands of concurrent updates to the same key using the shared session pool.
    Each request adds a unique nested field.

    Verify that:
    1. Every request succeeds.
    2. No update is lost.
    3. Every field contains the expected value.
    4. The final number of fields matches the number of requests.
    """
    key = "stress_concurrent_merge"

    # Ensure a clean initial state.
    async with self.session.delete(CACHE_URL) as response:
      self.assertEqual(response.status, 200)

    num_requests = STRESS_REQUESTS

    log.info(
      "Starting concurrent deep merge stress test: "
      "%s requests",
      num_requests,
    )

    async def send_update(i: int):
      payload = {
        "updates": {
          f"update_{i}": {
            "id": i,
            "value": f"value_{i}",
          }
        }
      }

      try:
        # Use the shared session pool instead of creating a new session per request
        async with self.session.post(
            f"{CACHE_URL}/{key}",
            json = payload,
            timeout = aiohttp.ClientTimeout(total = 60),
        ) as response:
          text = await response.text()
          return i, response.status, text
      except Exception as exc:
        return i, None, str(exc)

    started_at = time.monotonic()

    results = await asyncio.gather(*(send_update(i) for i in range(num_requests)))

    elapsed = time.monotonic() - started_at

    # Check that every request succeeded.
    errors = [(i, status_code, detail) for i, status_code, detail in results if status_code != 200]

    self.assertEqual(
      len(errors),
      0,
      f"Failed requests: {errors[:20]}",
    )

    log.info(
      "Completed %s POST requests in %.2f seconds "
      "(%.1f requests/sec)",
      num_requests,
      elapsed,
      num_requests / elapsed if elapsed else 0,
    )

    # Verify the final stored state.
    async with self.session.get(
      f"{CACHE_URL}/{key}",
      timeout = aiohttp.ClientTimeout(total = 30),
    ) as response:
      self.assertEqual(response.status, 200)
      result = await response.json()

    updates = result.get("updates")

    self.assertIsInstance(updates, dict)

    # No updates may be lost.
    self.assertEqual(
      len(updates),
      num_requests,
      "Some updates were lost or duplicated",
    )

    # Verify every individual value.
    for i in range(num_requests):
      field = f"update_{i}"

      self.assertIn(
        field,
        updates,
        f"Missing field: {field}",
      )

      self.assertEqual(
        updates[field],
        {
          "id": i,
          "value": f"value_{i}",
        },
        f"Data corruption in field: {field}",
      )

    log.info(
      "PASS: all %s concurrent updates preserved",
      num_requests,
    )

  async def test_stress_concurrent_average_integrity(self):
    """
    STRESS / LOST UPDATE DETECTION:

    Concurrently increment count1 and count2 through the average API.

    Every request adds exactly 1 to count1 and 2 to count2.
    The final totals must account for every successful request.
    """
    key = "stress_concurrent_average"

    # Remove data left by a previous run.
    async with self.session.delete(
      f"{BASE_URL}/average/{key}",
      timeout = aiohttp.ClientTimeout(total = 30),
    ) as delete_response:
      self.assertIn(
        delete_response.status,
        (200, 404),
      )

    num_requests = STRESS_REQUESTS

    log.info(
      "Starting concurrent average stress test: "
      "%s requests",
      num_requests,
    )

    async def send_increment(i: int):
      try:
        async with self.session.post(
            f"{BASE_URL}/average/{key}/1/2",
            timeout = aiohttp.ClientTimeout(total = 60),
        ) as response:
          text = await response.text()
          return i, response.status, text
      except Exception as exc:
        return i, None, str(exc)

    started_at = time.monotonic()

    results = await asyncio.gather(*(send_increment(i) for i in range(num_requests)))

    elapsed = time.monotonic() - started_at

    errors = [(i, status_code, detail) for i, status_code, detail in results if status_code != 200]

    self.assertEqual(
      len(errors),
      0,
      f"Failed requests: {errors[:20]}",
    )

    log.info(
      "Completed %s average updates in %.2f seconds "
      "(%.1f requests/sec)",
      num_requests,
      elapsed,
      num_requests / elapsed if elapsed else 0,
    )

    # Verify the final state through the GET endpoint.
    async with self.session.get(
      f"{BASE_URL}/average/{key}",
      timeout = aiohttp.ClientTimeout(total = 30),
    ) as response:
      self.assertEqual(response.status, 200)
      result = await response.json()

    expected_count1 = num_requests
    expected_count2 = num_requests * 2
    expected_total = num_requests * 3
    expected_average = 1 / 3

    self.assertEqual(
      result["count1"],
      expected_count1,
      "Lost updates detected in count1",
    )

    self.assertEqual(
      result["count2"],
      expected_count2,
      "Lost updates detected in count2",
    )

    self.assertEqual(
      result["total"],
      expected_total,
      "Incorrect total after concurrent updates",
    )

    self.assertAlmostEqual(
      result["average"],
      expected_average,
      places = 10,
      msg = "Incorrect average after concurrent updates",
    )

    log.info(
      "PASS: count1=%s, count2=%s, total=%s, average=%s",
      result["count1"],
      result["count2"],
      result["total"],
      result["average"],
    )

    # Clean up.
    async with self.session.delete(
      f"{BASE_URL}/average/{key}",
      timeout = aiohttp.ClientTimeout(total = 30),
    ):
      pass

if __name__ == '__main__':
  logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
    datefmt = DeyeUtils.time_format_str,
  )

  DeyeTestUtils.setup_test_environment(log_name = Path(__file__).stem)
  DeyeTestUtils.turn_on_remote_cache()

  logger = logging.getLogger()

  if not DeyeLoggers().is_test_loggers:
    logger.error('ERROR: your loggers are not test loggers')
    sys.exit(1)

  with DeyeTestUtils.storage_server():
    unittest.main(verbosity = 2)
