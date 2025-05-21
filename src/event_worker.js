const admin = require("firebase-admin");
const mysql = require("mysql2/promise"); // Use promise-based MySQL

// Firebase Service Account Key
admin.initializeApp({
  credential: admin.credential.cert(require("./firebase-key.json")),
  databaseURL: "https://seniorproject-684c1.firebaseio.com"
});

const firestore = admin.firestore();

const connectionConfig = {
  host: "localhost",
  user: "root",
  password: "",
  database: "senior_project"
};

async function checkEventQueue() {
  const connection = await mysql.createConnection(connectionConfig);

  try {
    const [rows] = await connection.execute(
      "SELECT * FROM event_queue WHERE sent = FALSE ORDER BY timestamp ASC LIMIT 1"
    );

    if (rows.length === 0) return;

    const event = rows[0];
    const { id, temp, humidity, ec, ph, chemical, light } = event;

    // Check full abnormal conditions
    const isAbnormal =
      temp > 40 || temp < 10 ||
      humidity > 90 || humidity < 20 ||
      ph > 8 || ph < 5.5 ||
      ec > 3 || ec < 0.2 ||
      chemical > 50 || chemical < 5;

    if (isAbnormal) {
      let title = "Abnormal Sensor Alert";
      let content = "";

      // High/Low condition messages
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

    // Mark as sent
    await connection.execute("UPDATE event_queue SET sent = TRUE WHERE id = ?", [id]);

  } catch (error) {
    console.error("❌ ERROR:", error.message);
  } finally {
    await connection.end();
  }
}

// Run check every 1 second
setInterval(() => {
  checkEventQueue();
}, 1000);
