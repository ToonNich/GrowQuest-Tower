// connect_mysql_to_firebase.js

const admin = require("firebase-admin");
const mysql = require("mysql2");

// ตั้งค่า Firebase Admin SDK
admin.initializeApp({
  credential: admin.credential.cert(require("AIzaSyB6oeXokIhQuOj8RJ2mpXPqwqP10gD0Xd0")),
  databaseURL: "seniorproject-684c1"
});

const firestore = admin.firestore();

// ตั้งค่า MySQL
const connection = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: "",
  database: "senior_project"
});
// Query ข้อมูลล่าสุด
connection.query("SELECT * FROM Temperature ORDER BY timestamp DESC LIMIT 1", (err, results) => {
  if (err) throw err;
  const latest = results[0];
  console.log("Latest:", latest);

  // ตรวจสอบเงื่อนไขผิดปกติ เช่น อุณหภูมิ > 40°C หรือความชื้น < 20%
  if (latest.temp > 40 || latest.humidity < 20) {
    // เขียนการแจ้งเตือนเข้าสู่ Firebase
    firestore.collection("alerts").add({
      message: `อุณหภูมิ: ${latest.temp}°C, ความชื้น: ${latest.humidity}%`,
      timestamp: admin.firestore.Timestamp.now(),
      read: false
    }).then(() => {
      console.log("แจ้งเตือนถูกส่งไปยัง Firebase แล้ว");
    });
  }
});
