#include <Servo.h>

Servo servo1;
Servo servo2;

int minAngle = 0;
int maxAngle = 90;
float stepSize = 1;
int delayTime = 15;    

unsigned long previousMillis = 0;
float currentPos = 0;
int direction = 1;

void setup() {
  servo1.attach(13);
  servo2.attach(12);
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= delayTime) {
    previousMillis = currentMillis;

    servo1.write(currentPos);
    servo2.write(maxAngle - currentPos);

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
