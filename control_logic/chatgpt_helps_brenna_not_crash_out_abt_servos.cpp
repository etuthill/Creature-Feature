#include <Servo.h>

Servo myServo;

// Servo vars
float currentPos = 90;
float targetPos  = 90;
float speedDegPerSec = 60.0;

unsigned long lastServoUpdate = 0;
const unsigned long servoInterval = 20; // ms

// Serial debounce vars
unsigned long lastSerialCheck = 0;
const unsigned long serialInterval = 50;

void setup() {
  Serial.begin(9600);
  myServo.attach(9);
  myServo.write(currentPos);
}

void loop() {
  updateServo();
  checkSerial();
}

/* ---------- SERVO ---------- */
void updateServo() {
  unsigned long now = millis();
  if (now - lastServoUpdate >= servoInterval) {
    lastServoUpdate = now;

    if (currentPos == targetPos) return;

    float step = speedDegPerSec * (servoInterval / 1000.0);

    if (currentPos < targetPos)
      currentPos = min(currentPos + step, targetPos);
    else
      currentPos = max(currentPos - step, targetPos);

    myServo.write((int)currentPos);
  }
}

/* ---------- SERIAL ---------- */
void checkSerial() {
  unsigned long now = millis();
  if (now - lastSerialCheck < serialInterval) return;

  lastSerialCheck = now;

  while (Serial.available()) {
    char c = Serial.read();

    // Example command: M120\n
    if (c == 'M') {
      targetPos = Serial.parseInt();
    }
  }
}
