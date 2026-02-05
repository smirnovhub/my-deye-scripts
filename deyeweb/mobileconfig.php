<?php

/**
 * iOS Mobile Configuration Profile Generator.
 *
 * This script generates and serves a .mobileconfig file dynamically to iOS devices.
 * It performs the following steps:
 * 1. Sets appropriate headers for Apple configuration profiles and disables caching.
 * 2. Loads a local XML-based template and an icon file.
 * 3. Populates the template with the current site URL, generated UUIDs, and Base64 icon data.
 * 4. Outputs the final configuration for "Web Clip" installation.
 *
 * @package    DeyeWeb
 * @author     Dmitry Smirnov
 * @version    1.0.0
 * @dependency php/utils.php (provides getSiteName, getFileAsBase64Mime, getFakeUuid)
 */

// File names
$config_file_name = 'deyeweb.mobileconfig';
$config_template_file_name = 'ios/deyeweb.mobileconfig.template';
$icon_file_name = 'ios/deyeweb_icon.png';

ob_start();

header('Content-Type: application/x-apple-aspen-config');
header('Content-Disposition: inline; filename="' . $config_file_name . '"');

header('Cache-Control: no-cache, no-store, must-revalidate');
header('Pragma: no-cache');
header('Expires: 0');

require_once(__DIR__ . '/php/utils.php');

function error(string $message)
{
  header('Content-Type: text/plain; charset=utf-8');
  header('Content-Disposition: inline');

  echo $message;

  header('Content-Length: ' . ob_get_length());
  ob_end_flush();

  exit;
}

// Check if template exists
if (!file_exists($config_template_file_name)) {
  error("Error: template file not found.");
}

// Check if icon exists
if (!file_exists($icon_file_name)) {
  error("Error: icon file not found.");
}

// Read template content and icon
$content = file_get_contents($config_template_file_name);
$icon = getFileAsBase64Mime($icon_file_name);

// Replace placeholders
$content = str_replace('TARGET_URL', getSiteName(), $content);
$content = str_replace('RANDOM_UUID_1', getFakeUuid(), $content);
$content = str_replace('RANDOM_UUID_2', getFakeUuid(), $content);
$content = str_replace('ICON_BASE64_DATA', trim($icon), $content);

// Output result
echo $content;

header('Content-Length: ' . ob_get_length());
ob_end_flush();
