#include <OneWire.h>
#include <DallasTemperature.h>
#include <Stepper.h>

// ----------- Pins -----------
#define ONE_WIRE_BUS 2    // DS18B20
#define PH_PIN A0         // pH Sensor
#define EC_PIN A1         // EC Sensor

#define IN1 8             // Pump control
#define IN2 9

// Stepper setup
const int stepsPerRevolution = 2048;
Stepper stepper(stepsPerRevolution, 4, 6, 5, 7);

// DS18B20 setup
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(9600);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  sensors.begin();
  stepper.setSpeed(10);

  Serial.println("GrowQuest Tower System Initialized");
}

void loop() {
  // ---- Read DS18B20 Temperature ----
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);

  // ---- Read pH ----
  int phRaw = analogRead(PH_PIN);
  float phVoltage = phRaw * (5.0 / 1023.0);
  float pH = 7 + ((2.5 - phVoltage) * 3.0); // Rough estimate

  // ---- Read EC ----
  int ecRaw = analogRead(EC_PIN);
  float ecVoltage = ecRaw * (5.0 / 1023.0);

  // ---- Log values ----
  Serial.print("Temp: "); Serial.print(tempC); Serial.print(" °C | ");
  Serial.print("pH: "); Serial.print(pH, 2); Serial.print(" | ");
  Serial.print("EC Raw: "); Serial.print(ecRaw);
  Serial.print(" | EC Voltage: "); Serial.print(ecVoltage, 2); Serial.println(" V");

  // ---- Trigger Pump if EC low ----
  if (ecVoltage < 2.0) {
    Serial.println("🔁 Low EC: Pumping nutrients...");

    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    delay(5000);  // Pump ON for 5s

    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    Serial.println("✅ Pump OFF");

    // ---- Rotate Stepper After Dosing ----
    Serial.println("↻ Rotating stepper...");
    stepper.step(stepsPerRevolution);    // Full turn
    delay(1000);
    stepper.step(-stepsPerRevolution);   // Return
  }

  delay(3000); // 3-second wait between readings
}
