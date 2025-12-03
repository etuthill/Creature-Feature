#include <Wire.h>
#include <Adafruit_MotorShield.h>

// Initialize button pins
int clawClosedButton = 2;  // Button to close the claw
int modeButton = 3;        // Button to toggle mode
int clawOpenButton = 4;    // Button to open the claw

// Initialize variables to keep track of the mode and value received over I2C
bool modeType = true;      // Mode type. Let's system know if joystick inputs should be sent to the lift or to the gantry 
int receivedValue = 0;     // Value received from I2C communication

// Initialize DC motors using the Adafruit library
Adafruit_MotorShield AFMS = Adafruit_MotorShield(); // Motor shield 
Adafruit_DCMotor *clawMotor = AFMS.getMotor(3);     // Claw motor on port 3
Adafruit_DCMotor *pulleyMotor = AFMS.getMotor(4);   // Pulley motor on port 4

void setup() {
  // Begin I2C communication with address 7
  Wire.begin(7);  
  Wire.onReceive(receiveData);  // Set up function to handle received data

  // Initialize the motor shield
  if (!AFMS.begin()) {
    Serial.println("Could not find Motor Shield. Check wiring.");
    while (1); // Stop execution if shield initialization fails
  }

  // Configure buttons as inputs with internal pull-up resistors
  pinMode(clawClosedButton, INPUT_PULLUP);
  pinMode(modeButton, INPUT_PULLUP);
  pinMode(clawOpenButton, INPUT_PULLUP);

  // Set initial motor states to off
  clawMotor->setSpeed(0);
  clawMotor->run(RELEASE);

  pulleyMotor->setSpeed(0);
  pulleyMotor->run(RELEASE);
}

// Function to handle data received over I2C
void receiveData(int byteCount) {
  while (Wire.available()) {
    receivedValue = Wire.read();  // Read received value
  }
}

void loop() {
  // Check if the claw closed button is pressed
  if (digitalRead(clawClosedButton) == LOW) {
    clawMotor->setSpeed(255); 
    clawMotor->run(BACKWARD); // Close the claw
  }

  // Check if the claw open button is pressed
  if (digitalRead(clawOpenButton) == LOW) {
    clawMotor->setSpeed(255); 
    clawMotor->run(FORWARD);  // Open the claw
  }

  // Check if the mode button is pressed
  if (digitalRead(modeButton) == LOW) {
    modeType = !modeType; // Toggle mode type
    Wire.beginTransmission(8); // Send mode change to device at address 8, gantry system
    Wire.write(modeType ? 21 : 22); // Send what mode gantry should be in
    Wire.endTransmission();
  }

  // Handle pulley motor based on what mode system is in
  if (!modeType) {
    if (receivedValue == 3) {
      pulleyMotor->setSpeed(255); 
      pulleyMotor->run(BACKWARD); // Move pulley backward
    } else if (receivedValue == 4) {
      pulleyMotor->setSpeed(255); 
      pulleyMotor->run(FORWARD);  // Move pulley forward
    } else {
      pulleyMotor->setSpeed(0);   
      pulleyMotor->run(RELEASE); // Stop the pulley motor
    }
  }
}