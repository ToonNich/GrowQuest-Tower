<?php
// เชื่อมต่อฐานข้อมูล
require 'DbConnection.php';

// ตรวจสอบการส่งข้อมูลจากฟอร์ม
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // รับข้อมูลจากฟอร์ม
    $characterName = $_POST['characterName'];  // ชื่อตัวละคร
    $characterImage = $_POST['characterImage'];  // ตัวละครที่เลือก

    // รับข้อมูลจาก session หรือระบบจัดการผู้ใช้
    session_start();
    $userID = $_SESSION['userID'];  // สมมติว่า userID ถูกเก็บใน session หลังจากการลงทะเบียน

    // เวลาที่ตัวละครถูกสร้าง
    $createdAt = date('Y-m-d H:i:s');

    // SQL เพื่อบันทึกข้อมูลตัวละคร
    $stmt = $conn->prepare("INSERT INTO character (User_ID, Name, Image, Created_at) VALUES (?, ?, ?, ?)");
    $stmt->bind_param("isss", $userID, $characterName, $characterImage, $createdAt);

    if ($stmt->execute()) {
        // หากบันทึกสำเร็จ
        echo json_encode(['success' => true]);
    } else {
        // หากบันทึกไม่สำเร็จ
        echo json_encode(['success' => false, 'message' => 'ไม่สามารถบันทึกข้อมูลได้']);
    }

    $stmt->close();
    $conn->close();
}
?>
