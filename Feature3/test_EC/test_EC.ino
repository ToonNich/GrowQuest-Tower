int ecPin = A1;  // EC sensor connected to analog pin A1

void setup() {
  Serial.begin(9600);
  Serial.println("EC Sensor Test Started");
}

void loop() {
  int rawValue = analogRead(ecPin);               // Read analog value
  float voltage = rawValue * (5.0 / 1023.0);       // Convert to voltage

  Serial.print("Raw Value: ");
  Serial.print(rawValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage, 2);
  Serial.println(" V");

  delay(1000);  // Read every second
}
