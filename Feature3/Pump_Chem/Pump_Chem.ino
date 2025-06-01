int IN1 = 8;  // L298N IN1
int IN2 = 9;  // L298N IN2

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  Serial.begin(9600);  // Start Serial Monitor
  Serial.println("Peristaltic Pump Control Initialized");
}

void loop() {
  // Turn pump ON
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  Serial.println("Pump ON (Forward) for 20 seconds");
  delay(50000);  // 20 seconds

  // Turn pump OFF
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  Serial.println("Pump OFF for 10 seconds");
  delay(5000);  // 10 seconds
}
