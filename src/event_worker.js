const admin = require("firebase-admin");

// กำหนด path ของไฟล์ Service Account Key ของ Firebase
const serviceAccount = require("./firebase-key.json");

// เริ่มต้น Firebase Admin SDK
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://seniorproject-684c1.firebaseio.com"
});

const firestore = admin.firestore();

async function checkMainCollection() {
  try {
    // ดึงเอกสารที่ sent = false เรียงตาม timestamp เก่าไปใหม่ 1 ตัว
    const snapshot = await firestore
      .collection("Main")
      .where("sent", "==", false)
      .orderBy("timestamp", "asc")
      .limit(1)
      .get();

    if (snapshot.empty) {
      // ไม่มีเอกสารที่ยังไม่ได้ส่ง
      return;
    }

    const doc = snapshot.docs[0];
    const event = doc.data();
    const docId = doc.id;

    // ดึงค่าจากเอกสาร
    const { temp, humidity, ec, ph, chemical, light } = event;

    // ตรวจสอบความผิดปกติของค่าต่างๆ
    const isAbnormal =
      temp > 40 || temp < 10 ||
      humidity > 90 || humidity < 20 ||
      ph > 8 || ph < 5.5 ||
      ec > 3 || ec < 0.2 ||
      chemical > 50 || chemical < 5;

    if (isAbnormal) {
      let title = "Abnormal Sensor Alert";
      let content = "";

      if (temp > 40) {
        title = "Temperature too high";
        content = `Temperature exceeds normal level: ${temp} °C`;
      } else if (temp < 10) {
        title = "Temperature too low";
        content = `Temperature is below normal level: ${temp} °C`;
      } else if (humidity > 90) {
        title = "Humidity too high";
        content = `Humidity exceeds normal range: ${humidity} %`;
      } else if (humidity < 20) {
        title = "Humidity too low";
        content = `Humidity is below normal range: ${humidity} %`;
      } else if (ph > 8) {
        title = "pH too high";
        content = `pH is too alkaline: ${ph}`;
      } else if (ph < 5.5) {
        title = "pH too low";
        content = `pH is too acidic: ${ph}`;
      } else if (ec > 3) {
        title = "EC too high";
        content = `Electrical Conductivity is too high: ${ec}`;
      } else if (ec < 0.2) {
        title = "EC too low";
        content = `Electrical Conductivity is too low: ${ec}`;
      } else if (chemical > 50) {
        title = "Chemical level too high";
        content = `Chemical concentration is too high: ${chemical}`;
      } else if (chemical < 5) {
        title = "Chemical level too low";
        content = `Chemical concentration is too low: ${chemical}`;
      }

      const message = `Alert: ${content}`;

      // บันทึกแจ้งเตือนไปยัง collection alerts
      await firestore.collection("alerts").add({
        title,
        content,
        message,
        values: { temp, humidity, ec, ph, chemical, light },
        timestamp: admin.firestore.Timestamp.now(),
        read: false
      });

      console.log("📢 Alert sent to Firebase:", message);
    }

    // อัปเดตเอกสารใน Main ว่าได้ส่งแจ้งเตือนแล้ว
    await firestore.collection("Main").doc(docId).update({ sent: true });

  } catch (error) {
    console.error("❌ ERROR:", error.message);
  }
}

// ทำงานทุก 1 วินาที
setInterval(() => {
  checkMainCollection();
}, 1000);
