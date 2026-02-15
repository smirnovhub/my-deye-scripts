<?php

// Start buffering the entire script output
ob_start();

require_once(__DIR__ . '/php/constants.php');
require_once(__DIR__ . '/php/utils.php');

// When renaming, don't forget to also change in deye_web_constants.py
$cacheFileName = sys_get_temp_dir() . '/deyeweb_cache.txt';
$command = PYTHON_CMD . ' ' . escapeshellarg(__DIR__ . '/front.py') . ' 2>&1';

startSession();
closeSession();

$content = '';
$isCached = true;

$isNeedResetCache = isCacheClearRequested();
if ($isNeedResetCache) {
  $isNeedUpdateCache = needUpdateCache($cacheFileName, FRONT_CACHE_MINIMUM_TIME_FOR_RESET_SEC);
  if ($isNeedUpdateCache) {
    $isCached = false;
    $content = executeCommandAndUpdateCacheWithLock($cacheFileName, $command, true);
  }
}

if ($content == '') {
  $isCached = true;
  $content = getCacheFileContentWithLock($cacheFileName);
}

if ($content == '') {
  $isCached = false;
  $content = executeCommandAndUpdateCacheWithLock($cacheFileName, $command, true);
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

<body style="background-color: #ffffff;">
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

if (canGzipStr($rawOutput)) {
  $finalOutput = gzencode($rawOutput);
  header('Content-Encoding: gzip');
}

// Set time limit for script execution
set_time_limit(FRONT_CACHE_UPDATE_EXECUTION_TIMEOUT_SEC);

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
  $isNeedUpdateCache = needUpdateCache($cacheFileName, FRONT_CACHE_UPDATE_TIME_SEC);
  if ($isNeedUpdateCache) {
    executeCommandAndUpdateCacheWithLock($cacheFileName, $command, false);
  }
}

?>