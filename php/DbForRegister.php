<?php
// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

date_default_timezone_set("Asia/Bangkok");
require "DbConnection.php";  // ถ้าไฟล์ DbConnection.php อยู่ในโฟลเดอร์เดียวกัน


// รับข้อมูลจากฟอร์ม
$username = $_POST['Username'];
$password = $_POST['Password'];
$email = $_POST['Email'];
$time = date('Y-m-d H:i:s'); // เวลาปัจจุบัน

// ตรวจสอบว่า Password และ ConfirmPassword ตรงกันหรือไม่
$confirmPassword = $_POST['ConfirmPassword'];
if ($password !== $confirmPassword) {
    die("❌ Password และ Confirm Password ไม่ตรงกัน");
}

// เข้ารหัสรหัสผ่าน
$hashedPassword = password_hash($password, PASSWORD_DEFAULT);

// สร้างคำสั่ง SQL สำหรับการแทรกข้อมูล
$sql = "INSERT INTO users (Username, Password, Email, Time) 
        VALUES (?, ?, ?, ?)";


$stmt = $conn->prepare($sql);
$stmt->bind_param("ssss", $username, $hashedPassword, $email, $time);

if ($stmt->execute()) {
    header("Location: ../LoginPage.html");
    exit();
} else {
    echo "❌ เกิดข้อผิดพลาดในการลงทะเบียน: " . $stmt->error;
}

// ปิดการเชื่อมต่อ
$stmt->close();
$conn->close();
?>
