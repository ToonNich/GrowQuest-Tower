const admin = require('firebase-admin');
const { getFirestore, Timestamp } = require('firebase-admin/firestore');

// 🔐 ใส่ path ไปยัง serviceAccountKey ของคุณ
const serviceAccount = require('./firebase-key.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = getFirestore();

const readingsRef = db.collection('tubeData')
  .doc('zG3FGDcmT7hEImtzCKiY73HhGOs2')
  .collection('readings');

async function generateMockData() {
  // กำหนดเวลาปัจจุบัน
  const now = new Date();

  // สร้าง baseTime เป็นวันที่วันนี้ เวลา 19:30:00
  const baseTime = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
    21, 0, 0, 0
  );

  const intervalMs = 60 * 60 * 1000 / 120; // 30 วินาทีต่อชุด = 120 ชุด/ชม

  for (let i = 0; i < 120; i++) {
    const fakeData = {
      chem_tank: getRandomFloat(0, 100),
      ec: getRandomFloat(50, 100),
      hum: getRandomFloat(20, 100),
      light: getRandomInt(0, 1000),        // light อาจจะเก็บเป็น int ก็ได้
      main_tank: getRandomFloat(0, 100),
      ph: getRandomFloat(0, 14),
      temp: getRandomFloat(20, 80),
      timestamp: Timestamp.fromDate(new Date(baseTime.getTime() + i * intervalMs))
    };

    await readingsRef.add(fakeData);
    console.log(`Mock data ${i + 1}/120 created`);
  }

  console.log('✅ Done creating mock data');
}

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRandomFloat(min, max) {
  return +(Math.random() * (max - min) + min).toFixed(2);
}

generateMockData();
