<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $input_text = $_POST['input-text'];
  $time = date('Y-m-d H:i:s');  // 获取当前时间
  $file_path = '123.txt';
$ip_address = $_SERVER['REMOTE_ADDR'];
  $content = $input_text . "\n" . $time . "    " . $ip_address . "\n";  // 添加换行符和时间
  file_put_contents($file_path, $content, FILE_APPEND);
}
?>
