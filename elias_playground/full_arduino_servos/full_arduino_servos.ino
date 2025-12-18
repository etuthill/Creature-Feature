#include <Servo.h>
#include <Adafruit_NeoPixel.h>

void resetMachine();

const unsigned long debounceDelay = 40; // ms
unsigned long lastForceDisturbance = 0;
bool forceActive = false;

unsigned long eatExitTime = 0;
bool eatCooldownArmed = false;

bool inputLocked = false; // lock inputs during REACTING

struct DebouncedButton {
  int pin;
  bool stableState;
  bool lastReading;
  unsigned long lastChangeTime;
};

// led strip
#define NUM_LEDS 3
#define DATA_PIN 13
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_RGB + NEO_KHZ800);

// map pins
const int forceSensor = A0;
const int hallSensor  = A1;

// sensor vars
int hallMin = 325;
int hallMax = 675;
int forceThreshold = 1000;

// debounce interactions
const unsigned long eatCooldown = 1000;
const unsigned long petCooldown = 500;

bool wasEating = false;

// fluctuation buffer
int hallMinLo = hallMin - 30;
int hallMaxHi = hallMax + 30;

// servos
Servo leftServo;
Servo rightServo;
Servo backServo;

int servoStartPos = 90;

// smooth servo vars
int leftCurrentPos  = servoStartPos;
int rightCurrentPos = servoStartPos;
int backCurrentPos  = servoStartPos;

int leftTargetPos  = servoStartPos;
int rightTargetPos = servoStartPos;
int backTargetPos  = servoStartPos;

bool servosEnabled = false;

const unsigned long servoInterval = 20;
const float speedDegPerSec = 30.0;

unsigned long lastLeftServoUpdate  = 0;
unsigned long lastRightServoUpdate = 0;
unsigned long lastBackServoUpdate  = 0;

// buttons
const int foodButton = 4;
const int playButton = 3;
const int backButton = 2;

DebouncedButton foodBtn  = { foodButton, HIGH, HIGH, 0 };
DebouncedButton playBtn  = { playButton, HIGH, HIGH, 0 };
DebouncedButton backBtn  = { backButton, HIGH, HIGH, 0 };

enum State { IDLE, HALL, FORCE, REACTING };
State state = IDLE;

// remember which interaction we're finishing
char pendingDone = '\0';

int LEDsaveState[2][3] = {
  {0,255,0}, // food
  {0,255,0}, // bored
};

void setup() {
  // Serial
  Serial.begin(9600);
  Serial.flush();

  // LED strip
  strip.begin();
  strip.setPixelColor(2, strip.Color(0,255,0));
  strip.setPixelColor(1, strip.Color(0,255,0));
  strip.setPixelColor(0, strip.Color(0,0,0));
  strip.show();

  // initialize I/O pins
  pinMode(forceSensor, INPUT);
  pinMode(hallSensor, INPUT);
  pinMode(foodButton, INPUT_PULLUP);
  pinMode(playButton, INPUT_PULLUP);
  pinMode(backButton, INPUT_PULLUP);

  //Down down
  leftServo.attach(11);
  //Down down
  rightServo.attach(10);
  //Down down
  backServo.attach(12);

  // set servos to initial positions
  leftServo.write(servoStartPos);
  rightServo.write(servoStartPos);
  backServo.write(servoStartPos);
}

void loop() {
  checkSerialAndState();
  updateServos();   // only active in REACTING
}

bool buttonPressed(DebouncedButton &btn) {
  bool reading = digitalRead(btn.pin);

  if (reading != btn.lastReading) {
    btn.lastChangeTime = millis();
  }

  if ((millis() - btn.lastChangeTime) > debounceDelay) {
    if (reading != btn.stableState) {
      btn.stableState = reading;
      if (btn.stableState == LOW) {
        btn.lastReading = reading;
        return true;
      }
    }
  }

  btn.lastReading = reading;
  return false;
}

void checkSerialAndState() {

  // block inputs while reacting
  bool foodPressed = !inputLocked && buttonPressed(foodBtn);
  bool playPressed = !inputLocked && buttonPressed(playBtn);
  bool backPressed = !inputLocked && buttonPressed(backBtn);

  ////////////////////////////////////////////////////////////////////////////////////////////////
  // SERIAL FSM CONTROL 

  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "RESET") {
      resetMachine();
      return;
    }

    char cmdType = '\0';
    char specific = '\0';

    if (cmd.length() >= 3 && cmd[1] == ':') {
      cmdType  = cmd[0];
      specific = cmd[2];
    }

    if (cmdType == 'S') {
      switch (specific) {
        case 'i':
          state = IDLE;
          inputLocked = false;
          strip.setPixelColor(2, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
          strip.setPixelColor(1, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
          strip.setPixelColor(0, strip.Color(0,0,0));
          strip.show();
          break;

        case 'h':
          state = HALL;
          strip.setPixelColor(2, strip.Color(0,0,0));
          strip.setPixelColor(1, strip.Color(0,0,0));
          strip.setPixelColor(0, strip.Color(0,0,255));
          strip.show();
          break;

        case 'f':
          state = FORCE;
          strip.setPixelColor(2, strip.Color(0,0,0));
          strip.setPixelColor(1, strip.Color(0,0,0));
          strip.setPixelColor(0, strip.Color(0,0,255));
          strip.show();
          break;

        case 'r':
          state = REACTING;
          inputLocked = true;
          servosEnabled = true;
          strip.setPixelColor(2, strip.Color(0,0,0));
          strip.setPixelColor(1, strip.Color(0,0,0));
          strip.setPixelColor(0, strip.Color(0,0,0));
          strip.show();
          break;
      }
    }

    if (cmdType == 'D') {
      switch (specific) {
        case 'h':
          LEDsaveState[0][0] = min(255, LEDsaveState[0][0] + 15);
          LEDsaveState[0][1] = max(0,   LEDsaveState[0][1] - 15);
          strip.setPixelColor(2, strip.Color(
            LEDsaveState[0][0],
            LEDsaveState[0][1],
            LEDsaveState[0][2]));
          strip.show();
          break;

        case 'f':
          LEDsaveState[1][0] = min(255, LEDsaveState[1][0] + 15);
          LEDsaveState[1][1] = max(0,   LEDsaveState[1][1] - 15);
          strip.setPixelColor(1, strip.Color(
            LEDsaveState[1][0],
            LEDsaveState[1][1],
            LEDsaveState[1][2]));
          strip.show();
          break;
      }
    }
  }

  ////////////////////////////////////////////////////////////////////////////////////////////////
  // READINGS AND REACTIONS 

  if (state == HALL && backPressed) {
    Serial.println("hi");
  }
  else if (state == HALL) {

    int hallReading = analogRead(hallSensor);
    bool isEating = (hallReading < hallMinLo || hallReading > hallMaxHi);
    unsigned long now = millis();

    if (isEating && !wasEating) {
      Serial.println("he");
      eatCooldownArmed = false;
    }

    if (!isEating && wasEating) {
      eatExitTime = now;
      eatCooldownArmed = true;
    }

    if (eatCooldownArmed && (now - eatExitTime >= eatCooldown)) {
      eatCooldownArmed = false;

      LEDsaveState[0][0] = 0;
      LEDsaveState[0][1] = 255;
      strip.setPixelColor(2, strip.Color(0,255,0));
      strip.show();

      Serial.println("ef");
      startReaction('e');
    }

    wasEating = isEating;
  }

  else if (state == FORCE && backPressed) {
    Serial.println("fi");
  }
  else if (state == FORCE) {

    int forceReading = analogRead(forceSensor);
    bool disturbed = (forceReading < forceThreshold);
    unsigned long now = millis();

    if (disturbed) {
      lastForceDisturbance = now;
      if (!forceActive) {
        forceActive = true;
        Serial.println("fp");
      }
    }

    if (forceActive && !disturbed &&
        (now - lastForceDisturbance >= petCooldown)) {

      forceActive = false;

      LEDsaveState[1][0] = 0;
      LEDsaveState[1][1] = 255;
      strip.setPixelColor(1, strip.Color(0,255,0));
      strip.show();

      Serial.println("pp");
      startReaction('p');
    }
  }

  else if (state == IDLE) {
    if (foodPressed) Serial.println("ih");
    else if (playPressed) Serial.println("if");
  }
}

void startReaction(char type) {
  state = REACTING;
  inputLocked = true;
  pendingDone = type;

  leftTargetPos  = 89;
  rightTargetPos = 89;
  backTargetPos  = 45;

  servosEnabled = true;
}

void updateServos() {
  /**
  Moves servos to a target position (or back to start position if already in target)
  * Behavior:
  *   - Returns if servos disabled
  *   - uses moveServoSmooth to move servos
  *   - When all servos reach their targets:
  *       * If target was not 90, resets target to 90
  *       * If target was 90, ends by
  *         disabling servos, unlocking inputs to allow interaction, sending "pd" or "ed" to update state machine
  * should be called repeatedly from loop() 
    */
  if (!servosEnabled) return;

  moveServoSmooth(leftServo,  leftCurrentPos,  leftTargetPos,  lastLeftServoUpdate);
  moveServoSmooth(rightServo, rightCurrentPos, rightTargetPos, lastRightServoUpdate);
  moveServoSmooth(backServo,  backCurrentPos,  backTargetPos,  lastBackServoUpdate);

  if (leftCurrentPos == leftTargetPos &&
      rightCurrentPos == rightTargetPos &&
      backCurrentPos == backTargetPos) {

    if (leftTargetPos != servoStartPos || rightTargetPos != servoStartPos || backTargetPos != servoStartPos) {
      leftTargetPos  = servoStartPos;
      rightTargetPos = servoStartPos;
      backTargetPos  = servoStartPos;
    } else {
      servosEnabled = false;
      inputLocked = false;

      if (pendingDone == 'e') Serial.println("ed");
      if (pendingDone == 'p') Serial.println("pd");

      pendingDone = '\0';
    }
  }
}

void moveServoSmooth(Servo &servo, int &currentPos, int targetPos,
                     unsigned long &lastUpdate) {
  /**
 * Smoothly moves servo towards target position.
 *
 * Changes servo position in small steps at a fixed time interval,
 * producing non-blocking, time-based motion. Updates until target is reached.

 * Args:
 *   servo: servo object
 *   currentPos: where servo is (changes by step)
 *   targetPos: where the servo is going 
 *   lastUpdate: timestamp of last update
 *
 * Behavior:
 *   - Returns if the update interval hasn't passed
 *   - Finds step size based on speedDegPerSec and servoInterval, - 1 degree minimum
 *   - Moves the servo toward the target position
 *   - Writes the updated position 
 *
 * should be called repeatedly - gets called from updateServos
 */

  unsigned long now = millis();
  if (now - lastUpdate < servoInterval) return;
  lastUpdate = now;

  if (currentPos == targetPos) return;

  // ensure we always move at least 1 degree
  int step = max(1, (int)(speedDegPerSec * servoInterval / 1000.0));

  if (currentPos < targetPos)
    currentPos = min(currentPos + step, targetPos);
  else
    currentPos = max(currentPos - step, targetPos);

  servo.write(currentPos);
}

void resetMachine() {
  state = IDLE;
  inputLocked = false;
  servosEnabled = false;
  pendingDone = '\0';

  leftCurrentPos  = servoStartPos;
  rightCurrentPos = servoStartPos;
  backCurrentPos  = servoStartPos;

  leftServo.write(servoStartPos);
  rightServo.write(servoStartPos);
  backServo.write(servoStartPos);

  strip.setPixelColor(2, strip.Color(0,255,0));
  strip.setPixelColor(1, strip.Color(0,255,0));
  strip.setPixelColor(0, strip.Color(0,0,0));
  strip.show();
}
