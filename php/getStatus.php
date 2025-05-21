<?php
header('Content-Type: application/json; charset=utf-8');

// ตั้งค่าการเชื่อมต่อ MySQL
$host = "localhost";
$user = "root";
$password = "";
$dbname = "senior_project";

// เชื่อมต่อ
$conn = new mysqli($host, $user, $password, $dbname);
$conn->set_charset("utf8"); // เพื่อรองรับภาษาไทย ถ้ามี

if ($conn->connect_error) {
  http_response_code(500);
  echo json_encode(["error" => "Connection failed: " . $conn->connect_error]);
  exit;
}

// ดึงข้อมูลล่าสุดจาก value_test
$sql = "SELECT EC, Humidity, Temperature FROM value_test ORDER BY value_test_ID DESC LIMIT 1";
$result = $conn->query($sql);

if ($result && $result->num_rows > 0) {
  echo json_encode($result->fetch_assoc());
} else {
  echo json_encode(["EC" => null, "Humidity" => null, "Temperature" => null]);
}

$conn->close();
?>
