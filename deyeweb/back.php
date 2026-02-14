<?php

// Start buffering the entire script output
ob_start();

require_once(__DIR__ . '/php/constants.php');
require_once(__DIR__ . '/php/utils.php');

startSession();

try {
  // Prepare JSON payload
  $json = file_get_contents('php://input');
  $jsonArray = parseAndValidateJson($json);
  $payload = prepareJsonPayload($jsonArray);

  closeSession();

  $command = PYTHON_CMD . ' ' . escapeshellarg(__DIR__ . '/back.py') . ' 2>&1';

  // Open Python process
  $process = proc_open(
    $command,
    [
      0 => ['pipe', 'r'], // stdin
      1 => ['pipe', 'w'], // stdout
    ],
    $pipes
  );

  if (!is_resource($process)) {
    echo getErrorMessage('Error: failed to start python process');
  } else {
    // Send JSON payload to Python
    fwrite($pipes[0], $payload);
    fclose($pipes[0]);

    try {
      // Read response from Python
      echo readPipeWithTimeout($pipes[1], 7);
    } catch (TimeoutException $e) {
      proc_terminate($process);
      echo getErrorMessage('Timeout: python process did not respond in time');
    } catch (Exception $e) {
      proc_terminate($process);
      echo getErrorMessage('Unexpected PHP error: ' . $e->getMessage());
    } finally {
      fclose($pipes[1]);
      proc_close($process);
    }
  }
} catch (Exception $e) {
  ob_clean();
  echo getErrorMessage($e->getMessage());
} finally {
  closeSession();
}

$rawOutput = ob_get_clean();
$finalOutput = $rawOutput;

if (strlen($rawOutput) > 1024) {
  $supportsGzip = isset($_SERVER['HTTP_ACCEPT_ENCODING']) && strpos($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip') !== false;
  if ($supportsGzip && function_exists('gzencode')) {
    $finalOutput = gzencode($rawOutput);
    header('Content-Encoding: gzip');
  }
}

// Required for Ajax requests to be parsed as JSON by browser
header('Content-Type: application/json; charset=utf-8');
header('Content-Length: ' . strlen($finalOutput));
header('Vary: Accept-Encoding');

echo $finalOutput;
