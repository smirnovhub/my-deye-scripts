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
 * Saves session data and closes the session to release the file lock.
 * This allows other concurrent AJAX requests to proceed while the
 * current script performs long-running operations (e.g., executing Python).
 * Note: Session data can still be read after this call, but not modified.
 *
 * @return void
 */
function closeSession(): void
{
  session_write_close();
}

/**
 * Processes and validates the incoming JSON payload.
 *
 * Ensures the input is a valid JSON string, checks for structural 
 * integrity, and verifies that the required business-level data 
 * is present before further processing.
 *
 * @param string $json
 * @return array
 */
function parseAndValidateJson(string $json): array
{
  if (empty(trim($json))) {
    throw new Exception('Error: JSON request is empty');
  }

  try {
    $jsonArray = json_decode($json, true, 5);
  } catch (\Throwable $e) {
    throw new Exception('Error: JSON decode error: ' . $e->getMessage());
  }

  if (json_last_error() !== JSON_ERROR_NONE) {
    $errorMessage = json_last_error_msg();
    throw new Exception('Error: JSON decode error: ' . $errorMessage);
  }

  if (!is_array($jsonArray)) {
    throw new Exception('Error: JSON request should be array');
  }

  if (!isset($jsonArray['command'])) {
    throw new Exception("Error: Missing 'command' field in JSON");
  }

  return $jsonArray;
}

/**
 * Prepares the array for transmission by injecting session metadata.
 *
 * Enriches the provided data with the current session identifier 
 * and converts the final structure into a JSON-formatted string.
 *
 * @param array $jsonArray
 * @return string
 */
function prepareJsonPayload(array $jsonArray): string
{
  $jsonArray['session_id'] = session_id();
  return json_encode($jsonArray);
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
 * Executes a shell command and updates the cache file using file locking.
 *
 * @param string $fileName The absolute path to the cache file.
 * @param string $command  The shell command to execute.
 * @param bool   $blocking Whether to wait for the lock or exit immediately if busy.
 * @return string The output of the executed command, or an empty string on failure 
 * or if the lock was not acquired in non-blocking mode.
 */
function executeCommandAndUpdateCacheWithLock(string $fileName, string $command, bool $blocking): string
{
  // 'c+' mode: Opens for reading/writing. 
  // Creates file if it doesn't exist. Does not truncate.
  $fp = fopen($fileName, "c+");
  if (!$fp) {
    return '';
  }

  $output = '';
  $flags = LOCK_EX;

  if (!$blocking) {
    $flags |= LOCK_NB;
  }

  try {
    if (flock($fp, $flags)) {
      try {
        $output = (string)shell_exec($command);
        if ($output != '') {
          ftruncate($fp, 0);
          rewind($fp);
          fwrite($fp, $output);
          fflush($fp);
        }
      } finally {
        flock($fp, LOCK_UN);
      }
    }
  } finally {
    fclose($fp);
  }

  return $output;
}

/**
 * Safely reads the contents of a cache file using a shared lock.
 *
 * @param string $fileName The absolute path to the cache file.
 * @return string The file contents, or an empty string if the file 
 * does not exist, is empty, or cannot be locked.
 */
function getCacheFileContentWithLock(string $fileName): string
{
  $isExists = file_exists($fileName);
  if (!$isExists) {
    return '';
  }

  $fp = fopen($fileName, "r");
  if (!$fp) {
    return '';
  }

  try {
    // Use shared lock (LOCK_SH) for reading
    if (flock($fp, LOCK_SH)) {
      try {
        // Clear stat cache to get actual file size
        clearstatcache(true, $fileName);
        $size = filesize($fileName);
        if ($size > 0) {
          return (string)fread($fp, $size);
        }
      } finally {
        flock($fp, LOCK_UN);
      }
    }
  } finally {
    fclose($fp);
  }

  return '';
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
  $response = [
    'error' => $message
  ];
  return json_encode($response);
}
