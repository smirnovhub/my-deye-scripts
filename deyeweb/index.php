<?php

// Start buffering the entire HTML output
ob_start();

require_once(__DIR__ . '/php/utils.php');

// When renaming, don't forget to also change in deye_web_constants.py
$cacheFile = '/tmp/deyeweb_cache.txt';
$command = __DIR__ . '/front.py 2>&1';

startSession();
closeSession();

$content = getCacheFileContentWithLock($cacheFile);
if ($content == '') {
  $content = executeCommandAndUpdateCacheWithLock($cacheFile, $command, true);
}

?>
<!DOCTYPE html>
<html>

<head>
  <title>Deye Web</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <link href="css/style.css" rel="stylesheet" type="text/css">
  <link href="css/spinner.css" rel="stylesheet" type="text/css">
</head>

<body style="background-color: #ffffff;" onload="onLoad()">
  <script src="js/script.js"></script>
  <script src="js/JsHttpRequest.js"></script>

  <?php
  echo $content;
  ?>

</body>

</html>

<?php
// Finalize the output buffer
$rawOutput = ob_get_clean();
$finalOutput = $rawOutput;

if (strlen($rawOutput) > 1024) {
  $supportsGzip = isset($_SERVER['HTTP_ACCEPT_ENCODING']) && strpos($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip') !== false;
  if ($supportsGzip && function_exists('gzencode')) {
    $finalOutput = gzencode($rawOutput);
    header('Content-Encoding: gzip');
  }
}

// Set time limit for script execution
set_time_limit(15);

// Keep script running after user disconnects
ignore_user_abort(true);

// Force connection close via HTTP headers
header('Content-Type: text/html; charset=utf-8');
header('Content-Length: ' . strlen($finalOutput));
header('Vary: Accept-Encoding');
header("Connection: close");

// Send data and flush buffers to the OS/Server
echo $finalOutput;

while (ob_get_level() > 0) {
  ob_end_flush();
}

flush();

// Background execution starts here
// The browser sees "Content-Length" and "Connection: close", so it stops waiting.
if ($isCached) {
  executeCommandAndUpdateCacheWithLock($cacheFile, $command, false);
}
?>