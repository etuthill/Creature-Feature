#include <Servo.h>

Servo servo1;
Servo servo2;

int minAngle = 0;
int maxAngle = 90;
int stepSize = 1;
int delayTime = 1;    

void setup() {
  servo1.attach(13);
  servo2.attach(12);
}

 

void loop() {
  for (float pos = minAngle; pos <= maxAngle; pos += stepSize) {
    servo1.writeMicroseconds(pos);
    servo2.writeMicroseconds(maxAngle - pos);
    delay(delayTime);
  }

  for (float pos = maxAngle; pos >= minAngle; pos -= stepSize) {
    servo1.writeMicroseconds(pos);
    servo2.writeMicroseconds(maxAngle - pos);
    delay(delayTime);
  }
}
