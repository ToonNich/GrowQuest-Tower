<?php
$host = "localhost";
$username = "root";
$password = "";
$database = "senior_project"; // ✅ เปลี่ยนเป็นชื่อฐานข้อมูลจริง

$conn = new mysqli($host, $username, $password, $database);

if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

$sql = "SELECT  EC, Humidity, Temperature, Ph FROM value_test ORDER BY value_test_ID DESC LIMIT 4"; // ✅ เปลี่ยนชื่อตารางจริง
$result = $conn->query($sql);

$data = [];
while ($row = $result->fetch_assoc()) {
  $data[] = $row;
}

header('Content-Type: application/json');
echo json_encode($data);
$conn->close();
?>
