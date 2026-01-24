<?php

require_once(__DIR__ . '/php/utils.php');
require_once(__DIR__ . '/php/JsHttpRequest.php');

startSession();

// Init JsHttpRequest and specify the encoding. It's important!
$JsHttpRequest = new JsHttpRequest('UTF-8');

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
  $GLOBALS['_RESULT']['error'] = 'Error: failed to start python process';
  exit;
}

// Prepare JSON payload
$payload = prepareJsonPayload($_POST);

// Send JSON payload to Python
fwrite($pipes[0], $payload);
fclose($pipes[0]);

try {
  // Read JSON response from Python
  $response = readPipeWithTimeout($pipes[1], 7);
  // Decode JSON response from Python
  $result = json_decode($response, true);
  $GLOBALS['_RESULT'] = $result;
} catch (TimeoutException $e) {
  proc_terminate($process);
  $GLOBALS['_RESULT']['error'] = 'Timeout: python process did not respond in time';
} catch (Exception $e) {
  proc_terminate($process);
  $GLOBALS['_RESULT']['error'] = 'Unexpected PHP error: ' . $e->getMessage();
} finally {
  fclose($pipes[1]);
  fclose($pipes[2]);
  proc_close($process);
}
