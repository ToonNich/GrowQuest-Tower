const admin = require("firebase-admin");
const serviceAccount = require("./firebase-key.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://seniorproject-684c1.firebaseio.com"
});

const firestore = admin.firestore();

async function checkMainCollection() {
  try {
    // ดึงข้อมูล Main ที่ sent == false เรียง timestamp
    const snapshot = await firestore
      .collection("Main")
      .where("sent", "==", false)
      .orderBy("timestamp", "asc")
      .limit(1)
      .get();

    if (snapshot.empty) {
      return;
    }

    const doc = snapshot.docs[0];
    const data = doc.data();
    const docId = doc.id;

    const { temp, humidity, ec, ph, chemical, light } = data;

    const isAbnormal =
      temp > 40 || temp < 10 ||
      humidity > 90 || humidity < 20 ||
      ph > 8 || ph < 5.5 ||
      ec > 3 || ec < 0.2 ||
      chemical > 50 || chemical < 5;

    if (!isAbnormal) {
      // ถ้าไม่ผิดปกติ อัปเดต sent = true เลย
      await firestore.collection("Main").doc(docId).update({ sent: true });
      return;
    }

    // กำหนดเนื้อหาการแจ้งเตือน
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

    const notificationData = {
      content,
      detailLink: "NotificationDetail.html",
      read: false,
      starred: false,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      title,
    };

    // ดึง userId ทั้งหมด (สมมติเก็บใน collection users)
    const usersSnapshot = await firestore.collection("users").get();

    if (usersSnapshot.empty) {
      console.log("ไม่มีผู้ใช้ในระบบ");
      return;
    }

    // สร้างแจ้งเตือนให้ผู้ใช้แต่ละคน
    const batch = firestore.batch();

    usersSnapshot.docs.forEach(userDoc => {
      const userId = userDoc.id;

      const notiRef = firestore
        .collection("notifications")
        .doc(userId)
        .collection("userNotifications")
        .doc(); // สร้าง id อัตโนมัติ

      batch.set(notiRef, notificationData);
    });

    // commit batch
    await batch.commit();

    // อัปเดตสถานะว่าแจ้งเตือนได้ส่งแล้ว
    await firestore.collection("Main").doc(docId).update({ sent: true });

    console.log(`Notifications created for ${usersSnapshot.size} users`);

  } catch (error) {
    console.error("Error in checkMainCollection:", error);
  }
}

setInterval(() => {
  checkMainCollection();
}, 1000);
