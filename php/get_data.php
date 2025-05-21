<?php
$host = "localhost";
$username = "root";
$password = "";
$database = "senior_project";

$conn = new mysqli($host, $username, $password, $database);
if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

// ปรับคำสั่ง SQL ให้ดึงข้อมูลแค่ 168 ข้อมูลล่าสุด
$sql = "SELECT EC, Humidity, Temperature, Ph FROM value_test ORDER BY value_test_ID DESC LIMIT 168";
$result = $conn->query($sql);

$data = [];
while ($row = $result->fetch_assoc()) {
  $data[] = $row;
}

header('Content-Type: application/json');
echo json_encode($data);
$conn->close();
?>
