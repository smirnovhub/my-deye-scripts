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
 *
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

function getErrorMessage(string $message): string
{
  $errorResponse = [
    'error'  => $message
  ];
  return json_encode($errorResponse);
}
