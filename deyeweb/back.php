<?php

// Required for Ajax requests to be parsed as JSON by browser
header('Content-Type: application/json; charset=utf-8');

require_once(__DIR__ . '/php/utils.php');

startSession();

// Open Python process
$process = proc_open(
  __DIR__ . '/back.py',
  [
    0 => ['pipe', 'r'], // stdin
    1 => ['pipe', 'w'], // stdout
    2 => ['pipe', 'w']  // stderr
  ],
  $pipes
);

// Check if process failed to start
if (!is_resource($process)) {
  // Output error and terminate script
  echo getErrorMessage('Error: failed to start python process');
  exit;
}

// Prepare JSON payload
$payload = prepareJsonPayload();

// Send JSON payload to Python
fwrite($pipes[0], $payload);
fclose($pipes[0]);

try {
  // Read JSON response from Python
  echo readPipeWithTimeout($pipes[1], 7);
} catch (TimeoutException $e) {
  proc_terminate($process);
  echo getErrorMessage('Timeout: python process did not respond in time');
} catch (Exception $e) {
  proc_terminate($process);
  echo getErrorMessage('Unexpected PHP error: ' . $e->getMessage());
} finally {
  fclose($pipes[1]);
  fclose($pipes[2]);
  proc_close($process);
}
