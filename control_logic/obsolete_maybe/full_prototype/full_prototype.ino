#include <Servo.h>

// setup servos
Servo servo1;
Servo servo2;

const int irPin = A0; 
int lastValue = -1; // store last smoothed value (IR)
const int alpha = 4; // smoothing factor for exponential smoothing (IR)

// LED setup
const int redLED = 11;
const int greenLED = 10;
const int blueLED = 9;

// motor speed/angle constraints
int minAngle1 = 60;  // servo1 range
int maxAngle1 = 90;

int minAngle2 = 60; // servo2 range 
int maxAngle2 = 90;

float stepSize = 1;
int delayTime = 15;   // motion speed (ms between steps)

// store current servo positions
float currentPos1 = minAngle1;
float currentPos2 = minAngle2;

// motion tracking
unsigned long previousMillis = 0;
int direction1 = 1;
int direction2 = -1;  // can start opposite if you like

void setup() {
  delay(1000);
  servo1.attach(13);
  servo2.attach(12);

  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(blueLED, OUTPUT);
}

void loop() {
  // read sensor 3 times (IR)
  int x = analogRead(irPin);
  int y = analogRead(irPin);
  int z = analogRead(irPin);

  // take min of the three reads (IR)
  int irValue = min(min(x, y), z);

  if (lastValue == -1) {
    // first run, just set baseline (IR)
    lastValue = irValue;
  } else {
    // apply exponential smoothing (IR)
    irValue = (irValue + alpha * lastValue) / (alpha + 1);
  }

  lastValue = irValue; // update stored value (IR)

  unsigned long currentMillis = millis();

  if (irValue < 550) { // object detected
    if (currentMillis - previousMillis >= delayTime) {
      previousMillis = currentMillis;

      // update servo 1
      currentPos1 += direction1 * stepSize;
      if (currentPos1 >= maxAngle1) {
        currentPos1 = maxAngle1;
        direction1 = -1;
      } else if (currentPos1 <= minAngle1) {
        currentPos1 = minAngle1;
        direction1 = 1;
      }

      // update servo 2 independently
      currentPos2 += direction2 * stepSize;
      if (currentPos2 >= maxAngle2) {
        currentPos2 = maxAngle2;
        direction2 = -1;
      } else if (currentPos2 <= minAngle2) {
        currentPos2 = minAngle2;
        direction2 = 1;
      }

      // write both
      servo1.write(currentPos1);
      servo2.write(currentPos2);
    }

    // green LED
    analogWrite(redLED, 0);
    analogWrite(greenLED, 100);
    analogWrite(blueLED, 0);

  } else {
    // stop servos (hold position)
    servo1.write(currentPos1);
    servo2.write(currentPos2);

    // red LED
    analogWrite(redLED, 100);
    analogWrite(greenLED, 0);
    analogWrite(blueLED, 0);
  }
}
