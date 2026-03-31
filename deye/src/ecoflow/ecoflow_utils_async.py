import aiohttp
import hashlib
import hmac
import random
import time
import binascii

from typing import Any, Dict, Optional, Union

class EcoflowUtilsAsync:
  @staticmethod
  def hmac_sha256(data: str, key: str) -> str:
    """
    Generate HMAC-SHA256 signature for a given string using a secret key.

    Args:
        data (str): The message/data to sign.
        key (str): The secret key used for signing.

    Returns:
        str: Hexadecimal representation of the HMAC-SHA256 signature.
    """
    hashed = hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()
    sign = binascii.hexlify(hashed).decode('utf-8')
    return sign

  @staticmethod
  def get_map(json_obj: Union[Dict[str, Any], list], prefix: str = "") -> Dict[str, Any]:
    """
    Flatten a nested JSON object (dict or list) into a single-level dict
    with compound keys representing the path to each value.

    Args:
        json_obj (dict or list): The JSON-like object to flatten.
        prefix (str, optional): Optional prefix for keys. Defaults to "".

    Returns:
        dict: A flattened dictionary with keys representing the nested path.
    """
    def flatten(obj: Any, pre: str = "") -> Dict[str, Any]:
      result: Dict[str, Any] = {}
      if isinstance(obj, dict):
        for k, v in obj.items():
          result.update(flatten(v, f"{pre}.{k}" if pre else k))
      elif isinstance(obj, list):
        for i, item in enumerate(obj):
          result.update(flatten(item, f"{pre}[{i}]"))
      else:
        result[pre] = obj
      return result

    return flatten(json_obj, prefix)

  @staticmethod
  def get_qstr(params: Dict[str, Any]) -> str:
    """
    Convert a dictionary into a query string with keys sorted alphabetically.

    Args:
        params (dict): Dictionary of key-value pairs.

    Returns:
        str: Query string in the form "key1=value1&key2=value2".
    """
    return '&'.join([f"{key}={params[key]}" for key in sorted(params.keys())])

  @staticmethod
  def get_headers(key: str, secret: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    Generate request headers including accessKey, nonce, timestamp, and HMAC-SHA256 signature.

    Args:
        key (str): API access key.
        secret (str): API secret for signing.
        params (dict, optional): Optional parameters to include in the signature. Defaults to None.

    Returns:
        dict: Headers dictionary with 'accessKey', 'nonce', 'timestamp', and 'sign'.
    """
    nonce = str(random.randint(100000, 999999))
    timestamp = str(int(time.time() * 1000))

    headers = {'accessKey': key, 'nonce': nonce, 'timestamp': timestamp}

    sign_str = ((EcoflowUtilsAsync.get_qstr(EcoflowUtilsAsync.get_map(params)) + '&' if params else '') +
                EcoflowUtilsAsync.get_qstr(headers))
    headers['sign'] = EcoflowUtilsAsync.hmac_sha256(sign_str, secret)

    return headers

  @staticmethod
  async def put_request(
    session: aiohttp.ClientSession,
    url: str,
    key: str,
    secret: str,
    params: Optional[Dict[str, Any]] = None,
  ) -> aiohttp.ClientResponse:
    """
    Send an HTTP PUT request with signed headers and optional JSON body.

    Args:
        url (str): URL to send the request to.
        key (str): API access key.
        secret (str): API secret for signing.
        params (dict, optional): Optional JSON body to include. Defaults to None.

    Returns:
        aiohttp.ClientResponse: Response object returned by the requests library.
    """
    headers = EcoflowUtilsAsync.get_headers(key, secret, params)
    return await session.put(url, json = params, headers = headers)

  @staticmethod
  async def get_request(
    session: aiohttp.ClientSession,
    url: str,
    key: str,
    secret: str,
    params: Optional[Dict[str, Any]] = None,
  ) -> aiohttp.ClientResponse:
    """
    Send an HTTP GET request with signed headers and optional JSON body.

    Args:
        url (str): URL to send the request to.
        key (str): API access key.
        secret (str): API secret for signing.
        params (dict, optional): Optional JSON body to include. Defaults to None.

    Returns:
        aiohttp.ClientResponse: Response object returned by the requests library.
    """
    headers = EcoflowUtilsAsync.get_headers(key, secret, params)
    return await session.get(url, json = params, headers = headers)

  @staticmethod
  async def post_request(
    session: aiohttp.ClientSession,
    url: str,
    key: str,
    secret: str,
    params: Optional[Dict[str, Any]] = None,
  ) -> aiohttp.ClientResponse:
    """
    Send an HTTP POST request with signed headers and optional JSON body.

    Args:
        url (str): URL to send the request to.
        key (str): API access key.
        secret (str): API secret for signing.
        params (dict, optional): Optional JSON body to include. Defaults to None.

    Returns:
        aiohttp.ClientResponse: Response object returned by the requests library.
    """
    headers = EcoflowUtilsAsync.get_headers(key, secret, params)
    return await session.post(url, json = params, headers = headers)
