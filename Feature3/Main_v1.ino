#include <OneWire.h>
#include <DallasTemperature.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_TSL2591.h>

// ----------- Pins -----------
#define ONE_WIRE_BUS 2     // DS18B20
#define PH_PIN A0          // pH Sensor
#define EC_PIN A1          // EC Sensor

#define IN3 3              // Pump control
#define IN4 4

#define DHTPIN 10          // DHT22 data pin
#define DHTTYPE DHT22

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

  sensors.begin();
  dht.begin();

  if (tsl.begin()) {
    Serial.println("TSL2591 Light Sensor Found");
    tsl.setGain(TSL2591_GAIN_MED);        // Options: LOW, MED, HIGH, MAX
    tsl.setTiming(TSL2591_INTEGRATIONTIME_100MS); // 100MS for decent speed + accuracy
  } else {
    Serial.println("⚠️ TSL2591 Not Detected");
  }

  Serial.println("GrowQuest Tower System Initialized (DS18B20 + DHT22 + IN3/IN4 + TSL2591)");
}

void loop() {
  // ---- Serial Command Listener ----
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "DOSE") {
      Serial.println("Command received: DOSE");
      runPump(15000);  // Run for 15 seconds
    }
    else {
      Serial.print("Unknown command: ");
      Serial.println(command);
    }
  }

  // ---- Read DS18B20 ----
  sensors.requestTemperatures();
  float tempC_DS18B20 = sensors.getTempCByIndex(0);

  // ---- Read DHT22 ----
  float tempC_DHT = dht.readTemperature();
  float humidity = dht.readHumidity();

  // ---- Read pH ----
  int phRaw = analogRead(PH_PIN);
  float phVoltage = phRaw * (5.0 / 1023.0);
  float pH = 7 + ((2.5 - phVoltage) * 3.0);

  // ---- Read EC ----
  int ecRaw = analogRead(EC_PIN);
  float ecVoltage = ecRaw * (5.0 / 1023.0);

  // ---- Read Light Sensor ----
  sensors_event_t lightEvent;
  tsl.getEvent(&lightEvent);
  float lux = lightEvent.light;

  // ---- Log all values ----
  Serial.print("DS18B20 Temp: "); Serial.print(tempC_DS18B20); Serial.print(" °C | ");
  Serial.print("DHT22 Temp: "); Serial.print(tempC_DHT); Serial.print(" °C | ");
  Serial.print("Humidity: "); Serial.print(humidity); Serial.print(" % | ");
  Serial.print("pH: "); Serial.print(pH, 2); Serial.print(" | ");
  Serial.print("EC Raw: "); Serial.print(ecRaw);
  Serial.print(" | EC Voltage: "); Serial.print(ecVoltage, 2); Serial.print(" V | ");
  Serial.print("Light: "); Serial.print(lux); Serial.println(" lux");

  // ---- Send JSON data for Firebase ----
  Serial.print("{\"temp\":");
  Serial.print(tempC_DS18B20);  // DS18B20 only
  Serial.print(",\"hum\":");
  Serial.print(humidity);       // DHT22
  Serial.print(",\"ph\":");
  Serial.print(pH, 2);
  Serial.print(",\"ec\":");
  Serial.print(ecVoltage, 2);
  Serial.print(",\"light\":");
  Serial.print(lux);
  Serial.println("}");

  // ---- Trigger Pump if EC low ----
  if (ecVoltage < 2.0) {
    Serial.println("🔁 Low EC: Pumping nutrients...");
    runPump(15000);  // Run for 15 seconds
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
