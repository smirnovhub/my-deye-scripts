<?php

class TimeoutException extends RuntimeException {}

/**
 * Starts a PHP session with a custom lifetime.
 *
 * @param int $days Number of days for the session to live.
 */
function startSession(int $days = 7): void
{
  // convert days to seconds
  $lifetime = $days * 24 * 60 * 60;

  // Set session lifetime
  ini_set('session.gc_maxlifetime', $lifetime);
  ini_set('session.cookie_lifetime', $lifetime);

  // Start the session
  session_start();
}

/**
 * Build a JSON-encoded payload with the current PHP session ID included.
 *
 * This function takes json parameter as string, adds the current PHP session ID
 * under the "session_id" key, and returns the resulting structure as a JSON string.
 *
 * @param string $json  Current payload as JSON string.
 * @return string  JSON-encoded payload containing the input parameters and session ID.
 */
function prepareJsonPayload(string $json): string
{
  $payloadArray = json_decode($json, true);

  if (!is_array($payloadArray)) {
    $payloadArray = [];
  }

  $payloadArray['session_id'] = session_id();
  return json_encode($payloadArray);
}

/**
 * Reads the output from a process pipe with a timeout.
 *
 * @param resource $pipe The pipe to read from (stdout of process).
 * @param int $timeout_sec Timeout in seconds.
 * @return string The data read from the pipe.
 * @throws TimeoutException if the operation times out.
 */
function readPipeWithTimeout($pipe, int $timeout_sec = 7): string
{
  // Set stdout to non-blocking
  stream_set_blocking($pipe, false);

  $response = '';
  $start = time();

  while (true) {
    $read = [$pipe];
    $write = null;
    $except = null;

    // Wait for data or timeout (0.2 sec)
    $num_changed_streams = stream_select($read, $write, $except, 0, 200000);

    if ($num_changed_streams === false) {
      // Error occurred
      break;
    }

    if ($num_changed_streams > 0) {
      $chunk = fread($pipe, 8192);
      if ($chunk === false || $chunk === '') {
        // Pipe closed, no more data
        break;
      }
      $response .= $chunk;
    }

    // Check for timeout
    if ((time() - $start) > $timeout_sec) {
      throw new TimeoutException("Process timed out after {$timeout_sec} seconds");
    }
  }

  return $response;
}

/**
 * Generates the base site URL including protocol, host, and the current directory path.
 * 
 * @return string The absolute base URL with a trailing slash.
 */
function getSiteName(): string
{
  $protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? "https://" : "http://";
  $host = $_SERVER['HTTP_HOST'];
  $path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
  $directory = trim(dirname($path), '/\\.');

  return $protocol . $host . '/' . ($directory ? $directory . '/' : '');
}

/**
 * Reads a file, encodes its content to Base64, and formats it according to RFC 2045.
 * 
 * @param string $filename The full path to the file to be processed.
 * @return string|bool The Base64 encoded string split into chunks, or false on failure.
 */
function getFileAsBase64Mime(string $filename)
{
  // Check if the file exists and is readable
  if (!file_exists($filename) || !is_readable($filename)) {
    return false;
  }

  // Read the binary content of the file
  $data = file_get_contents($filename);
  if ($data === false) {
    return false;
  }

  // Encode to Base64
  $base64 = base64_encode($data);

  // Split into 76-character chunks with CRLF for RFC 2045 compliance
  return chunk_split($base64, 76, "\n");
}

/**
 * Generates a pseudo-random UUID v4 string based on a unique identifier.
 * 
 * @return string A formatted uppercase UUID (e.g., 550E8400-E29B-41D4-A716-446655440000).
 */
function getFakeUuid(): string
{
  // Generates a random-like UUID v4
  return strtoupper(vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(md5(uniqid()), 4)));
}

/**
 * Wraps a plain text error message into a JSON-encoded string.
 *
 * @param string $message The error message to be included in the response.
 * @return string A JSON string containing the error key (e.g., {"error":"message"}).
 */
function getErrorMessage(string $message): string
{
  $errorResponse = [
    'error' => $message
  ];
  return json_encode($errorResponse);
}
