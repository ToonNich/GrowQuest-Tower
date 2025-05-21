const admin = require("firebase-admin");
const mysql = require("mysql2");

// โหลด Service Account Key จากไฟล์
admin.initializeApp({
  credential: admin.credential.cert(require("./firebase-key.json")),
  databaseURL: "https://seniorproject-684c1.firebaseio.com"
});

const firestore = admin.firestore();

// ตั้งค่าการเชื่อมต่อ MySQL
const connection = mysql.createConnection({
  host: "localhost",
  user: "root",
  password: "",
  database: "senior_project"
});

// ดึงข้อมูลล่าสุดจากตาราง value_test
connection.query("SELECT * FROM value_test ORDER BY timestamp DESC LIMIT 1", (err, results) => {
  if (err) throw err;

  const latest = results[0];
  console.log("Latest:", latest);

  // ดึงค่าจากคอลัมน์ (ปรับชื่อให้ตรงกับฐานข้อมูลจริงของคุณ)
  const { Temperature, Humidity, EC, Ph, Chemical } = latest;

  // เงื่อนไขค่าผิดปกติ (ตัวอย่าง)
  const isAbnormal =
    Temperature > 40 || Humidity < 20 || Ph < 5.5 || Ph > 8 || EC > 3 || Chemical === 'toxic';

  if (isAbnormal) {
    const msg = `แจ้งเตือน: Temp=${Temperature}°C, RH=${Humidity}%, pH=${Ph}, EC=${EC}, Chem=${Chemical}`;

    firestore.collection("alerts").add({
      message: msg,
      values: { Temperatureature, Humidity, EC, Ph, Chemical },
      timestamp: admin.firestore.Timestamp.now(),
      read: false
    }).then(() => {
      console.log("📢 แจ้งเตือนถูกส่งไปยัง Firebase แล้ว");
    });
  } else {
    console.log("✅ ข้อมูลปกติ ไม่ส่งแจ้งเตือน");
  }
});
