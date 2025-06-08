<?php
$host = "localhost";
$username = "root";
$password = "";
$database = "senior_project";

$conn = new mysqli($host, $username, $password, $database);
if ($conn->connect_error) {
  die("Connection failed: " . $conn->connect_error);
}

// ✅ Pull latest 168 records from long_term table
$sql = "SELECT EC, Humidity, Temperature, Ph, Light FROM long_term ORDER BY id DESC LIMIT 168";
$result = $conn->query($sql);

$data = [];
while ($row = $result->fetch_assoc()) {
  $data[] = $row;
}

header('Content-Type: application/json');
echo json_encode($data);
$conn->close();
?>
