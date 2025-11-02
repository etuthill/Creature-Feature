#include <Servo.h>

Servo motor1;
Servo motor2;

int minAngle = 0;
int maxAngle = 90;
int stepSize = 1;
int delayTime = 30;    

void setup() {
  motor1.attach(13);
  motor2.attach(12);
}

 

void loop() {
  for (float pos = minAngle; pos <= maxAngle; pos += stepSize) {
    motor1.write(pos);
    motor2.write(maxAngle - pos);
    delay(delayTime);
  }

  for (float pos = maxAngle; pos >= minAngle; pos -= stepSize) {
    motor1.write(pos);
    motor2.write(maxAngle - pos);
    delay(delayTime);
  }
}