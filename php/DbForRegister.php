<?php 
error_reporting(E_ALL);
ini_set('display_errors', 1);

date_default_timezone_set("Asia/Bangkok");
require "DbConnection.php";

$username = $_POST['Username'];
$password = $_POST['Password'];
$email = $_POST['Email'];
$confirmPassword = $_POST['ConfirmPassword'];
$time = date('Y-m-d H:i:s');

if ($password !== $confirmPassword) {
    echo json_encode([
        "success" => false,
        "message" => "❌ Password and Confirm Password not match"
    ]);
    exit();
}

$hashedPassword = password_hash($password, PASSWORD_DEFAULT);

$sql = "INSERT INTO users (Username, Password, Email, Time) VALUES (?, ?, ?, ?)";
$stmt = $conn->prepare($sql);
$stmt->bind_param("ssss", $username, $hashedPassword, $email, $time);

if ($stmt->execute()) {
    // เมื่อการลงทะเบียนสำเร็จ
    header("Location: ../LoginPage.html"); // เปลี่ยนหน้าไปที่ LoginPage.html
    exit();
} else {
    echo json_encode([
        "success" => false,
        "message" => "❌ Error: " . $stmt->error
    ]);
}

$stmt->close();
$conn->close();
?>
