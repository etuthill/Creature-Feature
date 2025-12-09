#include <Servo.h>

Servo servo1;   // pin 12
Servo servo2;   // pin 11
Servo servo3;   // pin 10

int minAngle = 0;
int maxAngle = 90;
float stepSize = 1;
int delayTime = 15;    

unsigned long previousMillis = 0;
float currentPos = 0;
int direction = 1;

void setup() {
  servo1.attach(12);
  servo2.attach(11);
  servo3.attach(10);
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= delayTime) {
    previousMillis = currentMillis;

    // servo motions
    servo1.write(currentPos);
    servo2.write(maxAngle - currentPos);
    servo3.write(currentPos);   // same direction as servo1 (change as needed)

    // sweep logic
    currentPos += direction * stepSize;

    if (currentPos >= maxAngle) {
      currentPos = maxAngle;
      direction = -1;
    } 
    else if (currentPos <= minAngle) {
      currentPos = minAngle;
      direction = 1;
    }
  }
}
