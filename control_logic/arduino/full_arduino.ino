#include <Servo.h>
#include <Adafruit_NeoPixel.h>

//ALL OF THIS NEEDS TO BE RESET SOMEHOW!!!!!!!!!

//led strip
#define NUM_LEDS 3
#define DATA_PIN 13
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_RGB + NEO_KHZ800);

//map pins
const int forceSensor = A0;
const int hallSensor = A1;

//sensor vars
int hallMin = 250;
int hallMax = 950;
int forceMin = 0;
int forceMax = 999;

// debounce interactions
unsigned long lastEatTime = 0;
const unsigned long eatCooldown = 500;
unsigned long lastPlayTime = 0;
const unsigned long playCooldown = 500;

bool wasEating = false;
bool wasPlaying = false;

// fluctuation buffer
int hallMinLo = hallMin - 30;
int hallMaxHi = hallMax + 30;

int forceMinLo = forceMin - 30;
int forceMaxHi = forceMax + 30;

//servos
Servo leftServo;
Servo rightServo;
Servo backServo;

//buttons
const int foodButton = 7;
const int playButton = 8;
const int backButton = 9;

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
  strip.setPixelColor(0, strip.Color(0,255,0)); // first LED GREEN
  strip.setPixelColor(1, strip.Color(0,255,0)); // second LED GREEN
  strip.setPixelColor(2, strip.Color(0,0,0)); // third LED off
  strip.show();

  //initialize I/O pins
  pinMode(forceSensor, INPUT);
  pinMode(hallSensor, INPUT);
  pinMode(foodButton, INPUT);
  pinMode(playButton, INPUT);
  pinMode(backButton, INPUT);

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

void loop() {
  checkSerialAndState();
  //if true use this anim loop
  //big statement
    
}

void checkSerialAndState() {
  //prob set anim states in here
  unsigned long now = millis();
  if (now - lastSerialCheck < serialInterval) return;

  lastSerialCheck = now;

  //read serial
  String cmd = Serial.readStringUntil('\n');
  char cmdType = cmd[0];
  char specific = cmd[3];
  //only true if state has CHANGED
  switch (cmdType) {
    case 'S':   // BUTTON commands
      switch (specific) {
        case 'i':
        // on h/b, off back button
          state = IDLE;
          strip.setPixelColor(0, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
          strip.setPixelColor(1, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
          strip.setPixelColor(2, strip.Color(0,0,0));
          strip.show();
          break;
        case 'h':
        // off h/b, on back button
          state = HALL;
          strip.setPixelColor(0, strip.Color(0,0,0));
          strip.setPixelColor(1, strip.Color(0,0,0));
          strip.setPixelColor(2, strip.Color(0,0,255));
          strip.show();
          break;
        case 'f':
          // off h/b, on back button
          state = FORCE;
          strip.setPixelColor(0, strip.Color(0,0,0));
          strip.setPixelColor(1, strip.Color(0,0,0));
          strip.setPixelColor(2, strip.Color(0,0,255));
          strip.show();
          break;
        case 'r':
          // off all
          state = REACTING;
          strip.setPixelColor(0, strip.Color(0,0,0));
          strip.setPixelColor(1, strip.Color(0,0,0));
          strip.setPixelColor(2, strip.Color(0,0,0));
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
          strip.setPixelColor(0, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
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
    case 'R':
      switch (specific) {
        case 'h':
          //reset food LED
          LEDsaveState[0][0] = 0;
          LEDsaveState[0][1] = 255;
          strip.setPixelColor(0, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
          strip.show();
          break;
        case 'f':
          //reset food LED
          LEDsaveState[1][0] = 0;
          LEDsaveState[1][1] = 255;
          strip.setPixelColor(0, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
          strip.show();
          break;
      }
      break;
    }

  ////////////////////////////////////////////////////////////////////////////////////////////////
  //readings and reactions
  if (state == HALL && digitalRead(backButton) == HIGH){
    //hall->idle
    Serial.println("hi");
  }
  else if (state == HALL){
    //read hall
    int hallReading = analogRead(hallSensor);
    bool isEating = (hallReading < hallMinLo || hallReading > hallMaxHi);

    unsigned long now_eat = millis();

    // enter eat
    if (isEating && !wasEating && (now_eat - lastEatTime > eatCooldown)) {
        Serial.println("he");
        lastEatTime = now_eat;
    }

    // exit eat (ate)
    if (!isEating && wasEating) {
        Serial.println("ef"); // print once
    }

    wasEating = isEating;
  }
  else if (state == FORCE){
    if (digitalRead(backButton) == HIGH){
      //force->idle
      Serial.println("fi");
    }
    else{
      //only do if still in this state
      //read force
      int forceReading = analogRead(forceSensor);
      if (forceReading > forceMin && forceReading < forceMax){
        //force->play react
        Serial.println("fp");
      }
    }
  }
  if (state == FORCE && digitalRead(backButton) == HIGH){
    //force->idle
    Serial.println("fi");
  }
  else if (state == FORCE){
    //force hall
    int forceReading = analogRead(forceSensor);
    bool isPlaying = (forceReading < forceMinLo || forceReading > forceMaxHi);

    unsigned long now_play = millis();

    // enter eat
    if (isPlaying && !wasPlaying && (now_play - lastPlayTime > playCooldown)) {
        Serial.println("fp");
        lastPlayTime = now_play;
    }

    // exit eat (ate)
    if (!isPlaying && wasPlaying) {
        Serial.println("pp"); // print once
    }

    wasPlaying = isPlaying;
  }
  else if (state == IDLE){
    //read h/b buttons
    if(digitalRead(foodButton) == HIGH){
      //idle->hall
      Serial.println("ih");
    }
    else if(digitalRead(playButton) == HIGH){
      //idle->force
      Serial.println("if");
    }
  }
}


//give each of these unique vars
//CHANGE THESE SO THEY WORK WITH 3 SERVOS UGHHHHHHH
void goToNeutral() {
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

void neutralToB() {
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

void boredToPlaySense() {
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

void boredToPlay() {
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

void hungryToEat() {
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

