#include <Stepper.h>

const int stepsPerRevolution = 2048;  // Depends on your stepper motor model

// Initialize the Stepper library with the pins connected to the driver
Stepper myStepper(stepsPerRevolution, 4, 6, 5, 7);

void setup() {
  Serial.begin(9600);
  Serial.println("Stepper Motor Test");
  myStepper.setSpeed(10);  // Set speed in RPM
}

void loop() {
  Serial.println("Rotating 1 revolution clockwise");
  myStepper.step(stepsPerRevolution);  // Rotate one full revolution clockwise
  delay(2000);

  Serial.println("Rotating 1 revolution counter-clockwise");
  myStepper.step(-stepsPerRevolution);  // Rotate one full revolution counter-clockwise
  delay(2000);
}
