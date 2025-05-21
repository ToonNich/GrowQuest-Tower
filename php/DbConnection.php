<?php
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "senior_project";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("❌ Connection failed: " . $conn->connect_error);
}
?>
