#include <OneWire.h>
#include <DallasTemperature.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_TSL2591.h>

// ----------- Pins -----------
#define ONE_WIRE_BUS 2      // DS18B20
#define PH_PIN A0           // pH Sensor
#define EC_PIN A1           // EC Sensor

#define IN3 3               // Pump control
#define IN4 4

#define DHTPIN 10           // DHT22 data pin
#define DHTTYPE DHT22

// --- NEW: Water Level Sensor Pins ---
// Array of pins for the Main Hydroponic Tank (10%, 50%, 100%)
const int mainTankPins[] = {22, 23, 24};

// Array of pins for the Chemical Tank (10%, 50%, 100%)
const int chemTankPins[] = {25, 26, 27};


// DS18B20 setup
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// DHT22 setup
DHT dht(DHTPIN, DHTTYPE);

// TSL2591 setup
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);


void setup() {
  Serial.begin(9600);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // --- NEW: Initialize water sensor pins ---
  for (int i = 0; i < 3; i++) {
    pinMode(mainTankPins[i], INPUT_PULLUP);
    pinMode(chemTankPins[i], INPUT_PULLUP);
  }

  sensors.begin();
  dht.begin();

  if (tsl.begin()) {
    Serial.println("TSL2591 Light Sensor Found");
    tsl.setGain(TSL2591_GAIN_MED);
    tsl.setTiming(TSL2591_INTEGRATIONTIME_100MS);
  } else {
    Serial.println("⚠️ TSL2591 Not Detected");
  }

  Serial.println("GrowQuest Tower System Initialized (All Sensors)");
}


void loop() {
  
  if (Serial.available()) {
  String command = Serial.readStringUntil('\n');
  command.trim();

  // ✅ Accept "DOSE" or "DOSE <ms>", no Serial prints (so your JSON stream stays clean)
  if (command.startsWith("DOSE")) {
    unsigned long ms = 3000;          // default dose
    int sp = command.indexOf(' ');
    if (sp > 0) {
      unsigned long v = command.substring(sp + 1).toInt();
      if (v > 0) ms = v;
    }
    // safety clamp
    if (ms < 200)   ms = 200;
    if (ms > 20000) ms = 20000;

    runPump(ms);                       // reuse your existing pump function
  }
  // else: silently ignore unknown commands
}


  // ---- Read all sensors ----
  sensors.requestTemperatures();
  float tempC_DS18B20 = sensors.getTempCByIndex(0);
  float tempC_DHT = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  int phRaw = analogRead(PH_PIN);
  float phVoltage = phRaw * (5.0 / 1023.0);
  float pH = 7 + ((2.5 - phVoltage) * 3.0);
  
  int ecRaw = analogRead(EC_PIN);
  float ecVoltage = ecRaw * (5.0 / 1023.0);
  
  sensors_event_t lightEvent;
  tsl.getEvent(&lightEvent);
  float lux = lightEvent.light;

  // --- NEW: Read Water Tank Levels ---
  int mainTankLevel = checkTankLevel(mainTankPins);
  int chemTankLevel = checkTankLevel(chemTankPins);


  // ---- Log all values for debugging ----
  Serial.print("DS18B20 Temp: "); Serial.print(tempC_DS18B20); Serial.print("°C | ");
  Serial.print("DHT22 Temp: "); Serial.print(tempC_DHT); Serial.print("°C | ");
  Serial.print("Humidity: "); Serial.print(humidity); Serial.print("% | ");
  Serial.print("pH: "); Serial.print(pH, 2); Serial.print(" | ");
  Serial.print("EC Voltage: "); Serial.print(ecVoltage, 2); Serial.print("V | ");
  Serial.print("Light: "); Serial.print(lux); Serial.print(" lux | ");
  // --- NEW: Add water levels to debug log ---
  Serial.print("Main Tank: "); Serial.print(mainTankLevel); Serial.print("% | ");
  Serial.print("Chem Tank: "); Serial.print(chemTankLevel); Serial.println("%");

  
  // ---- Send JSON data for Firebase ----
  Serial.print("{\"temp\":");
  Serial.print(tempC_DS18B20);
  Serial.print(",\"hum\":");
  Serial.print(humidity);
  Serial.print(",\"ph\":");
  Serial.print(pH, 2);
  Serial.print(",\"ec\":");
  Serial.print(ecVoltage, 2);
  Serial.print(",\"light\":");
  if (isnan(lux)) {
    Serial.print("0");  // fallback value if sensor fails
  } else {
    Serial.print(lux);
  }
  // --- NEW: Add water levels to JSON string ---
  Serial.print(",\"main_tank\":");
  Serial.print(mainTankLevel);
  Serial.print(",\"chem_tank\":");
  Serial.print(chemTankLevel);
  Serial.println("}");


  // ---- Trigger Pump if EC low ----
  if (ecVoltage < 2.0) {
    Serial.println("🔁 Low EC: Pumping nutrients...");
    runPump(15000);   // Run for 15 seconds
  }

  delay(3000); // 3 seconds between readings
}


// ---- Helper: Run Pump for specified ms ----
void runPump(int duration_ms) {
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  delay(duration_ms);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  Serial.println("✅ Pump cycle complete");
}


// --- NEW: Helper function to check tank levels ---
/**
 * Checks the status of three sensors for a single tank and returns the level.
 * @param pins - An array of 3 integer pin numbers [10%, 50%, 100%].
 * @return The calculated percentage (100, 50, 10, or 0).
 */
int checkTankLevel(const int pins[]) {
  // Remember: LOW means water is detected because we are using INPUT_PULLUP.
  bool level100 = (digitalRead(pins[2]) == LOW); // Top sensor
  bool level50  = (digitalRead(pins[1]) == LOW); // Middle sensor
  bool level10  = (digitalRead(pins[0]) == LOW); // Bottom sensor

  if (level100) {
    return 100;
  } else if (level50) {
    return 50;
  } else if (level10) {
    return 10;
  } else {
    return 0;
  }
}



