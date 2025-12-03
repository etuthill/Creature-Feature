#include <Wire.h>

// Pin assignments for stepper motors and buttons
const int stepX = 2;   // Step pin for X-axis motor
const int dirX  = 5;   // Direction pin for X-axis motor
const int stepY = 3;   // Step pin for Y-axis motor
const int dirY  = 6;   // Direction pin for Y-axis motor
const int stepZ = 4;   // Step pin for Z-axis motor
const int dirZ  = 7;   // Direction pin for Z-axis motor
const int enPin = 8;   // Enable pin for all motors

// Of note. The Z-axis motor is actually being used as an auxilary motor to help the X-axis motor move the gantry 

// Button pin assignments
int downButton = 10;   // Button to move downward
int rightButton = 9;   // Button to move right
int upButton = 11;     // Button to move upward
int leftButton = 12;   // Button to move left

// Variables to track motor state and movement
int x = 0; // Current X position
int y = 0; // Current Y position
unsigned long previousMicroX = 0; // Last time X-axis moved
unsigned long previousMicroY = 0; // Last time Y-axis moved

int delayStepper = 6000; // Delay between steps (in microseconds)

bool xMotorState = true; // Current state of X-axis motor
bool yMotorState = true; // Current state of Y-axis motor

int receivedValue = 21; // Value received over I2C. Set initally to 21 to set system to control gantry
unsigned long currentMicro; // Current microsecond timestamp

void setup() {
  Serial.begin(9600); // Initialize serial communication for debugging

  // Configure joystick pins as inputs with pull-up resistors
  pinMode(downButton, INPUT_PULLUP);
  pinMode(rightButton, INPUT_PULLUP);
  pinMode(upButton, INPUT_PULLUP);
  pinMode(leftButton, INPUT_PULLUP);

  // Configure motor control pins as outputs
  pinMode(stepX, OUTPUT);
  pinMode(dirX, OUTPUT);
  pinMode(stepY, OUTPUT);
  pinMode(dirY, OUTPUT);
  pinMode(stepZ, OUTPUT);
  pinMode(dirZ, OUTPUT);
  pinMode(enPin, OUTPUT);

  digitalWrite(enPin, LOW); // Enable all motors

  // Initialize I2C communication with address 8
  Wire.begin(8);
  Wire.onReceive(receiveData); // Set function to handle received data
}

// Function to handle data received over I2C
void receiveData(int byteCount) {
  while (Wire.available()) {
    receivedValue = Wire.read(); // Read the received value
  }
}

void loop() {
  currentMicro = micros(); // Get the current time

  if (receivedValue == 21) { // Check if system mode needs gantry to be controlled by joystick
    if (digitalRead(rightButton) == LOW) {
      digitalWrite(dirX, LOW); // Set X and Z directions to move right
      digitalWrite(dirZ, LOW);
      if ((currentMicro - previousMicroX) > delayStepper) {
        previousMicroX = currentMicro; // Update last move time
        xMotorState = !xMotorState; // Toggle motor pulse type
        digitalWrite(stepX, xMotorState ? HIGH : LOW);
        digitalWrite(stepZ, xMotorState ? HIGH : LOW);
        x -= 1; // Update X position
      }
    } else if (digitalRead(leftButton) == LOW) { 
      digitalWrite(dirX, HIGH); // Set X and Z directions to move left
      digitalWrite(dirZ, HIGH);
      if ((currentMicro - previousMicroX) > delayStepper) {
        previousMicroX = currentMicro; // Update last move time
        xMotorState = !xMotorState; // Toggle motor pulse type
        digitalWrite(stepX, xMotorState ? HIGH : LOW);
        digitalWrite(stepZ, xMotorState ? HIGH : LOW);
        x += 1; // Update X position
      }
    }

    if (digitalRead(downButton) == LOW) {
      digitalWrite(dirY, LOW); // Set Y direction to move downward
      if ((currentMicro - previousMicroY) > delayStepper) {
        previousMicroY = currentMicro; // Update last move time
        yMotorState = !yMotorState; // Toggle motor state
        digitalWrite(stepY, yMotorState ? HIGH : LOW);
        y -= 1; // Update Y position
      }
    } else if (digitalRead(upButton) == LOW) { 
      digitalWrite(dirY, HIGH); // Set Y direction to move upward
      if ((currentMicro - previousMicroY) > delayStepper) {
        previousMicroY = currentMicro; // Update last move time
        yMotorState = !yMotorState; // Toggle motor pulse type
        digitalWrite(stepY, yMotorState ? HIGH : LOW);
        y += 1; // Update Y position
      }
    }
  } else if (receivedValue == 22) { // Check if system mode needs to send joystick values to the lift
    // Transmit movement commands over I2C based on joystick
    if (digitalRead(leftButton) == LOW) {
      Wire.beginTransmission(7);
      Wire.write(3); // Send command for lift to move backward
      Wire.endTransmission();
    } else if (digitalRead(rightButton) == LOW) {
      Wire.beginTransmission(7);
      Wire.write(4); // Send command for lift to move forward
      Wire.endTransmission();
    } else {
      Wire.beginTransmission(7);
      Wire.write(0); // Send command for lift to stop
      Wire.endTransmission();
    }
  }
}