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
  const baseTime = new Date(); // เริ่มที่เวลาปัจจุบัน
  const intervalMs = 60 * 60 * 1000 / 120; // 30 วินาทีต่อชุด = 120 ชุด/ชม

  for (let i = 0; i < 120; i++) {
    const fakeData = {
      chem_tank: getRandomFloat(0, 100),
      ec: getRandomFloat(0.5, 3.0),
      hum: getRandomFloat(40, 90),
      light: getRandomInt(0, 1000),
      main_tank: getRandomFloat(0, 100),
      ph: getRandomFloat(4.0, 8.0),
      temp: getRandomFloat(20.0, 35.0),
      timestamp: Timestamp.fromDate(new Date(baseTime.getTime() + i * intervalMs))
    };

    await readingsRef.add(fakeData);
    console.log(`Mock data ${i + 1}/120 created`);
  }

  console.log('✅ Done creating mock data');
}

function getRandomFloat(min, max) {
  return +(Math.random() * (max - min) + min).toFixed(2);
}

function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

generateMockData();
