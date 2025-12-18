#include <Servo.h>
#include <Adafruit_NeoPixel.h>

void resetMachine();

const unsigned long debounceDelay = 40; // ms
unsigned long lastForceDisturbance = 0;
bool forceActive = false;

unsigned long eatExitTime = 0;
bool eatCooldownArmed = false;

struct DebouncedButton {
  int pin;
  bool stableState;
  bool lastReading;
  unsigned long lastChangeTime;
};

//led strip
#define NUM_LEDS 3
#define DATA_PIN 13
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_RGB + NEO_KHZ800);

//map pins
const int forceSensor = A0;
const int hallSensor = A1;

//sensor vars
int hallMin = 325;
int hallMax = 675;
int forceThreshold = 1000;

// debounce interactions
unsigned long lastEatTime = 0;
const unsigned long eatCooldown = 1000;
unsigned long lastPlayTime = 0;
const unsigned long playCooldown = 500;
const unsigned long petCooldown = 500;

bool wasEating = false;
bool wasPlaying = false;

// fluctuation buffer
int hallMinLo = hallMin - 30;
int hallMaxHi = hallMax + 30;

//servos
Servo leftServo;
Servo rightServo;
Servo backServo;

//buttons
const int foodButton = 4;
const int playButton = 3;
const int backButton = 2;

int servoStartPos = 90;

enum State { IDLE, HALL, FORCE, REACTING };
State state = IDLE;

int LEDsaveState[2][3] = {
  {0,255,0}, //food
  {0, 255, 0}, //bored
};

// Serial debounce vars
unsigned long lastSerialCheck = 0;
const unsigned long serialInterval = 50;


void setup() {
  //Serial
  Serial.begin(9600);
  Serial.flush();

  //LED strip
  strip.begin();
  strip.setPixelColor(2, strip.Color(0,255,0)); // first LED GREEN
  strip.setPixelColor(1, strip.Color(0,255,0)); // second LED GREEN
  strip.setPixelColor(0, strip.Color(0,0,0)); // third LED off
  strip.show();

  //initialize I/O pins
  pinMode(forceSensor, INPUT);
  pinMode(hallSensor, INPUT);
  pinMode(foodButton, INPUT_PULLUP);
  pinMode(playButton, INPUT_PULLUP);
  pinMode(backButton, INPUT_PULLUP);

  //set servo pins
  leftServo.attach(12);
  rightServo.attach(11);
  backServo.attach(10);

  //set servos to initial positions
  leftServo.write(servoStartPos);
  rightServo.write(servoStartPos);
  backServo.write(servoStartPos);
  delay(10000);
}


  DebouncedButton foodBtn  = { foodButton, HIGH, HIGH, 0 };
  DebouncedButton playBtn  = { playButton, HIGH, HIGH, 0 };
  DebouncedButton backBtn  = { backButton, HIGH, HIGH, 0 };

void loop() {
  checkSerialAndState();
  //if true use this anim loop
  //big statement
    
}

bool buttonPressed(DebouncedButton &btn) {
  bool reading = digitalRead(btn.pin);

  if (reading != btn.lastReading) {
    btn.lastChangeTime = millis();
  }

  if ((millis() - btn.lastChangeTime) > debounceDelay) {
    if (reading != btn.stableState) {
      btn.stableState = reading;
      if (btn.stableState == LOW) { // pressed
        btn.lastReading = reading;
        return true;
      }
    }
  }

  btn.lastReading = reading;
  return false;
}

void checkSerialAndState() {

  bool foodPressed = buttonPressed(foodBtn);
  bool playPressed = buttonPressed(playBtn);
  bool backPressed = buttonPressed(backBtn);

  String cmd = "";

 if (Serial.available() > 0) {
  cmd = Serial.readStringUntil('\n');
  cmd.trim();
  

    if (cmd == "RESET") {
      resetMachine();
      return;
      }
    }
  

  //read serial
  char cmdType  = '\0';
  char specific = '\0';

  if (cmd.length() >= 3 && cmd[1] == ':') {
    cmdType  = cmd[0];
    specific = cmd[2];
  }
   if (cmdType != '\0') {  
  //only true if state has CHANGED
    switch (cmdType) {
      case 'S':   // BUTTON commands
        switch (specific) {
          case 'i':
          // on h/b, off back button
            state = IDLE;
            strip.setPixelColor(2, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
            strip.setPixelColor(1, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
            strip.setPixelColor(0, strip.Color(0,0,0));
            strip.show();
            break;
          case 'h':
          // off h/b, on back button
            state = HALL;
            strip.setPixelColor(2, strip.Color(0,0,0));
            strip.setPixelColor(1, strip.Color(0,0,0));
            strip.setPixelColor(0, strip.Color(0,0,255));
            strip.show();
            break;
          case 'f':
            // off h/b, on back button
            state = FORCE;
            strip.setPixelColor(2, strip.Color(0,0,0));
            strip.setPixelColor(1, strip.Color(0,0,0));
            strip.setPixelColor(0, strip.Color(0,0,255));
            strip.show();
            break;
          case 'r':
            // off all
            state = REACTING;
            strip.setPixelColor(2, strip.Color(0,0,0));
            strip.setPixelColor(1, strip.Color(0,0,0));
            strip.setPixelColor(0, strip.Color(0,0,0));
            strip.show();
            break;
      }
      break; 
    case 'D':     
      switch (specific) {
        case 'h':
          //decrease food LED
          LEDsaveState[0][0] += 15;
          LEDsaveState[0][1] -= 15;
          if (LEDsaveState[0][0] > 255) LEDsaveState[0][0] = 255;
          if (LEDsaveState[0][1] < 0) LEDsaveState[0][1] = 0;
          strip.setPixelColor(2, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
          strip.show();
          break;
        case 'f':
          //decrease food LED
          LEDsaveState[1][0] += 15;
          LEDsaveState[1][1] -= 15;
          if (LEDsaveState[1][0] > 255) LEDsaveState[1][0] = 255;
          if (LEDsaveState[1][1] < 0) LEDsaveState[1][1] = 0;
          strip.setPixelColor(1, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
          strip.show();
          break;
      }
      break;
   }
  }

  ////////////////////////////////////////////////////////////////////////////////////////////////
  //readings and reactions
  if (state == HALL && backPressed) {
    Serial.println("hi");
  }
  else if (state == HALL){
    int hallReading = analogRead(hallSensor);
    bool isEating = (hallReading < hallMinLo || hallReading > hallMaxHi);
    unsigned long now = millis();

    // ENTER eating
    if (isEating && !wasEating) {
        Serial.println("he");
        eatCooldownArmed = false;
    }

    // EXIT eating -> arm cooldown
    if (!isEating && wasEating) {
        eatExitTime = now;
        eatCooldownArmed = true;
    }

    // COOLDOWN elapsed -> consume
    if (eatCooldownArmed && (now - eatExitTime >= eatCooldown)) {
        eatCooldownArmed = false;

        LEDsaveState[0][0] = 0;
        LEDsaveState[0][1] = 255;
        strip.setPixelColor(2, strip.Color(0,255,0));
        strip.show();

        Serial.println("ef");
        Serial.println("ed");
    }

    wasEating = isEating;

  }

  if (state == FORCE && backPressed) {
      Serial.println("fi");
  }
  else if (state == FORCE) {
      int forceReading = analogRead(forceSensor);
      bool disturbed = (forceReading < forceThreshold);  // petting detected
      unsigned long now = millis();

      if (disturbed) {
          lastForceDisturbance = now;

          if (!forceActive) {
              forceActive = true;
              Serial.println("fp"); // petting started
          }
      }

      // petting has stopped AND stayed stopped for petSettleTime
      if (forceActive && !disturbed &&
          (now - lastForceDisturbance >= petCooldown)) {

          forceActive = false;

          // consume the pet interaction ONCE
          LEDsaveState[1][0] = 0;
          LEDsaveState[1][1] = 255;
          strip.setPixelColor(1, strip.Color(
              LEDsaveState[1][0],
              LEDsaveState[1][1],
              LEDsaveState[1][2]
          ));
          strip.show();

          Serial.println("pp");
          Serial.println("pd");
      }
  }


    else if (state == IDLE) {
      if (foodPressed) {
        Serial.println("ih");
      }
      else if (playPressed) {
        Serial.println("if");
      }
    }
  }

void resetMachine() {
  state = IDLE;

  wasEating = false;
  wasPlaying = false;

  lastEatTime = 0;
  lastPlayTime = 0;

  LEDsaveState[0][0] = 0;
  LEDsaveState[0][1] = 255;
  LEDsaveState[0][2] = 0;

  LEDsaveState[1][0] = 0;
  LEDsaveState[1][1] = 255;
  LEDsaveState[1][2] = 0;

  strip.setPixelColor(2, strip.Color(0,255,0));
  strip.setPixelColor(1, strip.Color(0,255,0));
  strip.setPixelColor(0, strip.Color(0,0,0));
  strip.show();
}


//give each of these unique vars
//CHANGE THESE SO THEY WORK WITH 3 SERVOS UGHHHHHHH
// void goToNeutral() {
//   unsigned long now = millis();
//   if (now - lastServoUpdate >= servoInterval) {
//     lastServoUpdate = now;

//     if (currentPos == targetPos) return;

//     float step = speedDegPerSec * (servoInterval / 1000.0);

//     if (currentPos < targetPos)
//       currentPos = min(currentPos + step, targetPos);
//     else
//       currentPos = max(currentPos - step, targetPos);

//     myServo->write((int)currentPos);
//   }
// }

// void neutralToB() {
//   unsigned long now = millis();
//   if (now - lastServoUpdate >= servoInterval) {
//     lastServoUpdate = now;

//     if (currentPos == targetPos) return;

//     float step = speedDegPerSec * (servoInterval / 1000.0);

//     if (currentPos < targetPos)
//       currentPos = min(currentPos + step, targetPos);
//     else
//       currentPos = max(currentPos - step, targetPos);

//     myServo->write((int)currentPos);
//   }
// }

// void boredToPlaySense() {
//   unsigned long now = millis();
//   if (now - lastServoUpdate >= servoInterval) {
//     lastServoUpdate = now;

//     if (currentPos == targetPos) return;

//     float step = speedDegPerSec * (servoInterval / 1000.0);

//     if (currentPos < targetPos)
//       currentPos = min(currentPos + step, targetPos);
//     else
//       currentPos = max(currentPos - step, targetPos);

//     myServo->write((int)currentPos);
//   }
// }

// void boredToPlay() {
//   unsigned long now = millis();
//   if (now - lastServoUpdate >= servoInterval) {
//     lastServoUpdate = now;

//     if (currentPos == targetPos) return;

//     float step = speedDegPerSec * (servoInterval / 1000.0);

//     if (currentPos < targetPos)
//       currentPos = min(currentPos + step, targetPos);
//     else
//       currentPos = max(currentPos - step, targetPos);

//     myServo->write((int)currentPos);
//   }
// }

// void hungryToEat() {
//   unsigned long now = millis();
//   if (now - lastServoUpdate >= servoInterval) {
//     lastServoUpdate = now;

//     if (currentPos == targetPos) return;

//     float step = speedDegPerSec * (servoInterval / 1000.0);

//     if (currentPos < targetPos)
//       currentPos = min(currentPos + step, targetPos);
//     else
//       currentPos = max(currentPos - step, targetPos);

//     myServo->write((int)currentPos);
//   }
// }

