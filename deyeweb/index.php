<?php

require_once(__DIR__ . '/php/utils.php');
startSession();

?>
<!DOCTYPE html>
<html>

<head>
  <title>Deye Parameters</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <link href="css/style.css" rel="stylesheet" type="text/css">
  <link href="css/spinner.css" rel="stylesheet" type="text/css">
</head>

<body style="background-color: #ffffff;" onload="onLoad()">
  <script src="js/script.js"></script>
  <script src="js/JsHttpRequest.js"></script>

  <?php
  echo shell_exec(__DIR__ . '/front.py 2>&1');
  ?>

</body>

</html>
