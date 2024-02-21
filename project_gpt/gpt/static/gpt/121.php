<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
$user_agent = $_SERVER['HTTP_USER_AGENT'];

if (strpos($user_agent, 'iPhone') !== false) {
    $device_name = 'iPhone';
} elseif (strpos($user_agent, 'iPad') !== false) {
    $device_name = 'iPad';
} elseif (strpos($user_agent, 'Android') !== false) {
    $device_name = 'Android';
} else {
    $device_name = 'Unknown';
}
  $input_text = $_POST['input-text'];
$ip_address = $_SERVER['REMOTE_ADDR'];
  $time = date('Y-m-d H:i:s');  // 获取当前时间
  $file_path = '12.txt';
  $content = $input_text . "\n" . $time . "    " . $ip_address . "    " . $device_name . "\n" .  ;  // 添加换行符和时间
  file_put_contents($file_path, $content, FILE_APPEND);
  echo '留言成功';
}
?>
