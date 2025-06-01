void setup() {
  Serial.begin(9600);  // Start serial communication at 9600 baud
}

void loop() {
  int rawValue = analogRead(A0);  // Read analog value from pH sensor
  float voltage = rawValue * (5.0 / 1023.0);  // Convert ADC reading to voltage

  // Approximate pH calculation (needs calibration for accuracy)
  float pH = 7 + ((2.5 - voltage) * 3.0);

  Serial.print("Analog Value: ");
  Serial.print(rawValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage, 2);
  Serial.print(" V | Approximate pH: ");
  Serial.println(pH, 2);

  delay(1000);  // Wait 1 second before next reading
}
