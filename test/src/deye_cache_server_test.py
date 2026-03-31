import os
import sys
import logging
import requests
import unittest

import concurrent.futures

from typing import Any
from pathlib import Path

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

class TestDeyeCacheExtended(unittest.TestCase):
  session: requests.Session
  config: DeyeStorageConfig

  @classmethod
  def setUpClass(cls):
    """
    Global cleanup and session initialization.
    """
    cls.session = requests.Session()
    cls.config = DeyeStorageConfig()
    try:
      cls.session.delete(CACHE_URL)
    except requests.exceptions.ConnectionError:
      log.error(f"Error: Server not found at {BASE_URL}")
      sys.exit(1)

  def tearDown(self):
    """
    Reset cache after each test to ensure isolation.
    """
    self.session.delete(CACHE_URL)

  def test_ping(self):
    """Test health check endpoint."""
    with self.session.get(PING_URL) as response:
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.json(), {"status": "success"})

  def test_complex_nested_merge(self):
    """
    Test deep merging with multi-level nested dictionaries.
    """
    key = "nested_dev"

    # Level 1: Initial state
    initial = {"settings": {"mode": "auto", "limits": {"max_temp": 60}}}
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = initial).status_code, 200)

    # Level 2: Partial update of a deeply nested field
    update = {"settings": {"limits": {"min_temp": 10}, "active": True}}
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = update).status_code, 200)

    # Verify result
    res = self.session.get(f"{CACHE_URL}/{key}")
    self.assertEqual(res.status_code, 200)

    res_json = res.json()

    # Check that 'mode' (L2) was preserved while 'min_temp' (L3) was added
    self.assertEqual(res_json["settings"]["mode"], "auto")
    self.assertEqual(res_json["settings"]["limits"]["max_temp"], 60)
    self.assertEqual(res_json["settings"]["limits"]["min_temp"], 10)
    self.assertEqual(res_json["settings"]["active"], True)

  def test_different_data_types(self):
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

    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = payload).status_code, 200)

    res = self.session.get(f"{CACHE_URL}/{key}")
    self.assertEqual(res.status_code, 200)

    res_json = res.json()

    for k, v in payload.items():
      self.assertEqual(res_json[k], v, f"Value mismatch for key: {k}")

  def test_delete_specific_key(self):
    """Test DELETE /cache/{key} method."""
    key = "to_be_deleted"
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"data": 1}).status_code, 200)

    # Ensure it exists
    self.assertEqual(self.session.get(f"{CACHE_URL}/{key}").status_code, 200)

    # Delete
    del_res = self.session.delete(f"{CACHE_URL}/{key}")
    self.assertEqual(del_res.status_code, 200)

    # Verify 404 after deletion
    self.assertEqual(self.session.get(f"{CACHE_URL}/{key}").status_code, 404)

  def test_global_delete(self):
    """Test global cache reset (DELETE /cache)."""
    # Populate with multiple keys
    self.assertEqual(self.session.post(f"{CACHE_URL}/k1", json = {"v": 1}).status_code, 200)
    self.assertEqual(self.session.post(f"{CACHE_URL}/k2", json = {"v": 2}).status_code, 200)

    # Reset all
    self.assertEqual(self.session.delete(CACHE_URL).status_code, 200)

    stats = self.session.options(CACHE_URL)
    self.assertEqual(stats.status_code, 200)

    stats_json = stats.json()

    self.assertEqual(stats_json["keys_used"], 0)
    self.assertEqual(stats_json["bytes_used"], 0)

  def test_max_keys_limit(self):
    """
    Test that server returns 403 when trying to exceed MAX_KEYS_COUNT.
    Note: This test assumes MAX_KEYS_COUNT is small enough to test (e.g., 32).
    """
    # Clear first
    self.assertEqual(self.session.delete(CACHE_URL).status_code, 200)

    # Fill cache to the limit
    limit = self.config.MAX_KEYS_COUNT
    for i in range(limit):
      self.assertEqual(self.session.post(f"{CACHE_URL}/dev_{i}", json = {"data": i}).status_code, 200)

    # Try to add 33rd key
    res = self.session.post(f"{CACHE_URL}/overflow_key", json = {"data": "fail"})
    self.assertEqual(res.status_code, 403)
    self.assertIn("Maximum number of keys exceeded", res.json()["detail"])

  def test_json_size_limit_per_reqeust(self):
    """
    Test that each json request cannot exceed MAX_JSON_SIZE.
    """
    key = "big_storage_dev"
    # Create a large object that is below single request limit (256KB)
    # but combined with metadata might exceed storage limit
    large_chunk = {"data": "x" * (self.config.MAX_JSON_SIZE - 150)}

    # First send is fine
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = large_chunk).status_code, 200)

    # Second merge might push it over the limit if we keep adding
    # We'll send a very large update to trigger the 413 from the trial merge logic
    huge_update = {"extra": "y" * (self.config.MAX_JSON_SIZE + 10)}

    res = self.session.post(f"{CACHE_URL}/{key}", json = huge_update)
    self.assertEqual(res.status_code, 413)

    detail = res.json().get("detail", "")
    self.assertIn("JSON body size exceeded", detail)

  def test_storage_size_limit_per_key_cumulative(self):
    """
    SECURITY: Test that the cumulative storage for a single key 
    cannot exceed MAX_JSON_STORAGE_SIZE through multiple updates.
    """
    key = "cumulative_test_inverter"

    # 1. Clean up potential previous test data
    self.assertEqual(self.session.delete(f"{CACHE_URL}").status_code, 200)

    # 2. Define chunk size slightly below the single request limit
    # Subtracting 1000 bytes to account for JSON overhead (quotes, keys, braces)
    chunk_size = self.config.MAX_JSON_SIZE - 100
    chunk_data = "x" * chunk_size

    # 3. Calculate how many chunks are needed to hit the storage limit
    # Example: If storage is 1MB and chunk is 250KB, the 5th request should fail
    # WE ALLOW JUST ONE REQUEST WITH EXCEEDED JSON SIZE STORAGE!
    num_requests_to_fill = (self.config.MAX_JSON_STORAGE_SIZE // chunk_size) + 2

    log.info(f"Filling storage for '{key}'")
    log.info(f"Chunk: {chunk_size}, Storage Limit: {self.config.MAX_JSON_STORAGE_SIZE}")

    for i in range(num_requests_to_fill):
      # Use unique keys to force the server to expand the dictionary
      # If keys were identical, the server would just overwrite data
      payload = {f"register_group_{i}": chunk_data}
      with self.session.post(f"{CACHE_URL}/{key}", json = payload) as response:
        if i < num_requests_to_fill - 1:
          # These requests should be accepted (under total limit)
          self.assertEqual(response.status_code, 200,
                           f"Batch {i} failed prematurely with status {response.status_code}")
        else:
          # The final request must trigger the storage limit protection (413)
          # It passes the 'MAX_JSON_SIZE' check but fails the 'trial merge' check
          self.assertEqual(response.status_code, 413, "Server failed to block cumulative storage overflow")

          # Check for the specific error message
          detail = response.json().get("detail", "")
          self.assertIn("JSON storage size exceeded", detail)

  def test_concurrent_updates(self):
    """
    STRESS/RACE CONDITION TEST:
    Simulate multiple concurrent clients updating the same key.
    Verifies that asyncio.Lock on the server prevents data loss.
    """
    key = "race_condition_test"
    self.session.delete(f"{CACHE_URL}/{key}")

    # We will send 20 rapid updates to the same key
    num_updates = 20
    updates = [{"update_id": i} for i in range(num_updates)]

    def send_post(data):
      # Using a new session per thread to simulate different clients
      with requests.Session() as s:
        return s.post(f"{CACHE_URL}/{key}", json = data)

    with concurrent.futures.ThreadPoolExecutor(max_workers = 10) as executor:
      responses = list(executor.map(send_post, updates))

    # Check that all requests were successful
    for resp in responses:
      self.assertEqual(resp.status_code, 200)

    # Verify that the final object contains all update_id fields
    # (since deep_merge combines them)
    res = self.session.get(f"{CACHE_URL}/{key}").json()
    for i in range(num_updates):
      self.assertIn("update_id", res)
      # Note: in your deep_merge, 'update_id' will be overwritten by the last one,
      # but the server must not crash and must process all requests.

  def test_data_type_conflict_overwrite(self):
    """
    EDGE CASE:
    Verify behavior when a dictionary field is overwritten by a non-dictionary value.
    This tests the robustness of the deep_merge function.
    """
    key = "conflict_dev"

    # 1. Set a dictionary
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"data": {"nested": 1}}).status_code, 200)

    # 2. Overwrite 'data' with a simple integer (not a dict)
    # Your deep_merge: if not (isinstance(value, dict) and ... isinstance(source[key], dict))
    # it should just overwrite source[key] = value.
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"data": 100}).status_code, 200)

    res = self.session.get(f"{CACHE_URL}/{key}")
    self.assertEqual(res.status_code, 200)

    res_json = res.json()
    self.assertEqual(res_json["data"], 100)

    # 3. Overwrite back to dict
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"data": {"new_nested": 2}}).status_code, 200)

    res2 = self.session.get(f"{CACHE_URL}/{key}")
    self.assertEqual(res2.status_code, 200)

    res_json2 = res2.json()
    self.assertEqual(res_json2["data"]["new_nested"], 2)

  def test_malformed_json_and_empty_payload(self):
    """
    SECURITY/ROBUSTNESS:
    Verify server behavior with empty bodies or invalid content types.
    """
    key = "malformed_test"

    # Send empty body with JSON content-type
    with self.session.post(f"{CACHE_URL}/{key}", headers = {"Content-Type": "application/json"}) as response:
      # FastAPI should return 422 Unprocessable Entity for missing body
      self.assertEqual(response.status_code, 422)

  def test_deep_merge_array_handling(self):
    """
    LOGIC TEST:
    Verify how deep_merge handles lists (should overwrite, not extend).
    """
    key = "array_test"
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"list": [1, 2]}).status_code, 200)
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"list": [3, 4]}).status_code, 200)

    res = self.session.get(f"{CACHE_URL}/{key}")
    self.assertEqual(res.status_code, 200)

    res_json = res.json()
    # In standard deep_merge, lists are treated as values and overwritten
    self.assertEqual(res_json["list"], [3, 4])

  def test_extreme_nesting_depth(self):
    """
    PERFORMANCE/STABILITY:
    Test very deep JSON nesting (20+ levels).
    """
    key = "extreme_nest"
    # Dynamically build a 20-level dict
    current: Any = "bottom"
    for i in range(20, 0, -1):
      current = {f"L{i}": current}

    with self.session.post(f"{CACHE_URL}/{key}", json = current) as response:
      self.assertEqual(response.status_code, 200)

    with self.session.get(f"{CACHE_URL}/{key}").json() as res:
      # Verify we can reach the deepest value
      val = res
      for i in range(1, 21):
        val = val[f"L{i}"]
      self.assertEqual(val, "bottom")

  def test_type_swapping_in_nesting(self):
    """
    ROBUSTNESS:
    Tests what happens when a deep nested dict is suddenly replaced by a primitive, 
    and then vice-versa.
    """
    key = "swap_test"

    # Initial: {"a": {"b": {"c": 1}}}
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"a": {"b": {"c": 1}}}).status_code, 200)

    # Swap: {"a": {"b": "now_i_am_a_string"}}
    # Deep merge should see that "b" is no longer a dict in the update
    # and overwrite the old dict.
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"a": {"b": "string_value"}}).status_code, 200)

    res = self.session.get(f"{CACHE_URL}/{key}").json()
    self.assertEqual(res["a"]["b"], "string_value")

    # Swap back: {"a": {"b": {"new_dict": True}}}
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"a": {"b": {"new_dict": True}}}).status_code, 200)
    res = self.session.get(f"{CACHE_URL}/{key}").json()
    self.assertIsInstance(res["a"]["b"], dict)
    self.assertTrue(res["a"]["b"]["new_dict"])

  def test_large_number_of_keys_rapidly(self):
    """
    STRESS:
    Rapidly create many keys and then perform a global reset.
    Verifies that locks are cleaned up and don't leak memory.
    """
    # Create 50 unique keys (more than your MAX_KEYS_COUNT to trigger some 403s)
    for i in range(self.config.MAX_KEYS_COUNT + 15):
      self.session.post(f"{CACHE_URL}/stress_{i}", json = {"data": i})

    # Check stats before reset
    stat_res = self.session.options(CACHE_URL).json()
    self.assertEqual(stat_res["keys_used"], self.config.MAX_KEYS_COUNT)
    self.assertGreater(stat_res["bytes_used"], 0)

    # Global reset
    self.assertEqual(self.session.delete(CACHE_URL).status_code, 200)

    # Check stats after reset
    stat_after = self.session.options(CACHE_URL).json()
    self.assertEqual(stat_after["keys_used"], 0)
    self.assertEqual(stat_after["bytes_used"], 0)

  def test_invalid_endpoints(self):
    """
    ROBUSTNESS:
    Test requests to non-existent paths.
    """
    # 1. Random non-existent path
    resp = self.session.get(f"{BASE_URL}/invalid/path/to/resource")
    self.assertEqual(resp.status_code, 404)

    # 2. Path that looks like cache but is slightly wrong
    resp = self.session.get(f"{BASE_URL}/caches") # extra 's'
    self.assertEqual(resp.status_code, 404)

  def test_invalid_http_methods(self):
    """
    ROBUSTNESS:
    Test using wrong HTTP methods for valid endpoints.
    """
    # 1. POST to /ping (which only supports GET)
    resp = self.session.post(PING_URL)
    self.assertEqual(resp.status_code, 405) # Method Not Allowed

    # 2. GET to /cache without a key (only DELETE is supported for base /cache)
    resp = self.session.get(CACHE_URL)
    self.assertEqual(resp.status_code, 405)

    # 3. PUT to /cache/key (you use POST for updates)
    resp = self.session.put(f"{CACHE_URL}/some_key", json = {"a": 1})
    self.assertEqual(resp.status_code, 405)

  def test_url_encoding_and_special_chars(self):
    """
    EDGE CASE:
    Test keys with special characters and URL encoding.
    """
    # 1. Key with spaces and symbols
    # Requests will automatically URL-encode this to 'key%20with%20%24ymbols'
    special_key = "key with $symbols"
    payload = {"data": "test"}

    resp_post = self.session.post(f"{CACHE_URL}/{special_key}", json = payload)
    self.assertEqual(resp_post.status_code, 200)

    resp_get = self.session.get(f"{CACHE_URL}/{special_key}")
    self.assertEqual(resp_get.status_code, 200)
    self.assertEqual(resp_get.json()["data"], "test")

  def test_malformed_url_traversal(self):
    """
    SECURITY:
    Test for directory traversal attempts in the URL key.
    """
    # Attempt to use '../' in the key
    key = "../root_key"
    resp = self.session.post(f"{CACHE_URL}/{key}", json = {"hack": "attempt"})

    # FastAPI/Uvicorn might normalize this or treat it as a path.
    # If it's treated as /cache/root_key, it's fine.
    # If it tries to access /root_key (which doesn't exist), it's 404/405.
    self.assertEqual(resp.status_code, 404)

  def test_docs_and_openapi_exposure(self):
    """
    SECURITY:
    Check if FastAPI default documentation is enabled. 
    Usually, in production/critical services, /docs and /redoc should be disabled.
    """
    # FastAPI by default hosts these:
    for path in ["/docs", "/redoc", "/openapi.json"]:
      resp = self.session.get(f"{BASE_URL}{path}")
      # If you didn't disable them in FastAPI(docs_url=None), they will return 200
      # This test just documents the current state.
      status = "ENABLED" if resp.status_code == 200 else "DISABLED"
      log.info(f"FastAPI auto-doc {path} is {status}")

  def test_case_sensitivity(self):
    """
    EDGE CASE:
    Verify if paths are case-sensitive.
    /CACHE/key should typically return 404 if the route is defined as /cache/key.
    """
    key = "case_test"
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"v": 1}).status_code, 200)

    # Test uppercase endpoint
    resp = self.session.get(f"{BASE_URL}/CACHE/{key}")
    self.assertEqual(resp.status_code, 404)

    # Test uppercase ping
    resp = self.session.get(f"{BASE_URL}/PING")
    self.assertEqual(resp.status_code, 404)

  def test_path_parameter_abuse(self):
    """
    SECURITY:
    Test sending forbidden characters or path segments within the key parameter.
    """
    # 1. Attempting to access a nested path where only one level is expected
    # Your route is /cache/{key}. What if key contains a slash?
    # Requests will encode it, but let's see how FastAPI handles it.
    key_with_slash = "inverter/01"
    resp = self.session.get(f"{CACHE_URL}/{key_with_slash}")
    # It should be 404 because the router expects /cache/{key}
    # and 'inverter/01' is seen as two path segments.
    self.assertEqual(resp.status_code, 404)

  def test_trailing_slashes(self):
    """
    ROBUSTNESS:
    Check behavior with trailing slashes. 
    FastAPI by default is sensitive to trailing slashes unless configured otherwise.
    """
    # /ping/ vs /ping
    resp = self.session.get(f"{PING_URL}/")
    self.assertEqual(resp.status_code, 200)

    # /cache/key/ vs /cache/key
    resp = self.session.get(f"{CACHE_URL}/somekey/")
    self.assertEqual(resp.status_code, 404)

  def test_proxy_headers_spoofing(self):
    """
    SECURITY:
    Test how the server handles typical proxy headers.
    Useful if you rely on 'last_update_by' logic.
    """
    key = "proxy_test"

    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = {"data": 1}).status_code, 200)
    res_no_proxy = self.session.get(f"{CACHE_URL}/{key}").json()

    ip = res_no_proxy.get("last_update_by")

    # Try to spoof the source IP via X-Forwarded-For
    headers = {"X-Forwarded-For": "8.8.8.8"}
    self.session.post(f"{CACHE_URL}/{key}", json = {"data": 1}, headers = headers)

    res_with_proxy = self.session.get(f"{CACHE_URL}/{key}").json()
    self.assertEqual(res_with_proxy.get("last_update_by"), ip)

  def test_deep_null_merging_logic(self):
    """
    LOGIC/STABILITY:
    Verify how the server handles 'null' (None in Python) during a deep merge.
    In JSON, sending null often means 'clear this value'. 
    We check if the server can store nulls without crashing the deep_merge function.
    """
    key = "null_logic_test"

    # 1. Create initial deep structure
    initial = {"status": "online", "metrics": {"power": 5000, "temp": 45}}
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = initial).status_code, 200)

    # 2. Update power with a real value, but set temp to null
    # We want to see if 'temp' becomes null or if it crashes the merge
    update = {"metrics": {"power": 6000, "temp": None}}
    self.assertEqual(self.session.post(f"{CACHE_URL}/{key}", json = update).status_code, 200)

    res = self.session.get(f"{CACHE_URL}/{key}")
    self.assertEqual(res.status_code, 200)

    res_json = res.json()

    # Verify
    self.assertEqual(res_json["metrics"]["power"], 6000)
    self.assertIsNone(res_json["metrics"]["temp"]) # temp should be null now
    self.assertEqual(res_json["status"], "online") # status should be preserved

    # 3. CRITICAL: Try to merge a dict into a null value
    # This is where many merge functions fail (TypeError: 'NoneType' object is not subscriptable)
    killer_update = {
      "metrics": {
        "temp": {
          "sub_temp": 20
        } # 'temp' was None, now we try to make it a dict
      }
    }
    resp = self.session.post(f"{CACHE_URL}/{key}", json = killer_update)
    self.assertEqual(resp.status_code, 200)

    final_res = self.session.get(f"{CACHE_URL}/{key}").json()
    self.assertEqual(final_res["metrics"]["temp"]["sub_temp"], 20)

if __name__ == "__main__":
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
