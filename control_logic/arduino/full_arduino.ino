#include <Servo.h>
#include <Adafruit_NeoPixel.h>

//led strip
#define NUM_LEDS 3
#define DATA_PIN 13
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_GRB + NEO_KHZ800);

//map pins
const int forceSensor = A0;
const int hallSensor = A1;

//sensor vars
int hallMin = 0;
int hallMax = 999;
int forceMin = 0;
int forceMax = 99;

//servos
Servo leftServo;
Servo rightServo;
Servo backServo;

//buttons
const int foodButton = 7;
const int playButton = 8;
const int backButton = 9;

int servoStartPos = 90;

String state = String("idle");

int LEDsaveState[2][3] = {
  {0,255,0}, //food
  {0, 255, 0}, //bored
};


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
  delay(1000);
}

void loop() {
  //read serial
  if (Serial.available() >= 4) {      // wait for full 4-char command
    char cmd[4];
    for (int i = 0; i < 4; i++) {
      cmd[i] = Serial.read();
    }

    char cmdType = cmd[0];
    char specific = cmd[3];

    switch (cmdType) {
      case 'S':   // BUTTON commands
        switch (specific) {
          case 'i':
          // on h/b, off back button
            state = "idle";
            strip.setPixelColor(0, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
            strip.setPixelColor(1, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
            strip.setPixelColor(2, strip.Color(0,0,0));
            strip.show();
            break;
          case 'h':
          // off h/b, on back button
            state = "hall";
            strip.setPixelColor(0, strip.Color(0,0,0));
            strip.setPixelColor(1, strip.Color(0,0,0));
            strip.setPixelColor(2, strip.Color(0,0,255));
            strip.show();
            break;
          case 'f':
            // off h/b, on back button
            state = "force";
            strip.setPixelColor(0, strip.Color(0,0,0));
            strip.setPixelColor(1, strip.Color(0,0,0));
            strip.setPixelColor(2, strip.Color(0,0,255));
            strip.show();
            break;
          case 'r':
            // off all
            state = "reacting";
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
            strip.setPixelColor(0, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
            strip.show();
            break;
          case 'f':
            //decrease food LED
            LEDsaveState[1][0] += 15;
            LEDsaveState[1][1] -= 15;
            strip.setPixelColor(1, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
            strip.show();
            break;
        }
        break;
      case 'R':
        switch (specific) {
          case 'h':
            //reset food LED
            LEDsaveState[0][0] = 255;
            LEDsaveState[0][1] = 255;
            strip.setPixelColor(0, strip.Color(LEDsaveState[0][0],LEDsaveState[0][1],LEDsaveState[0][2]));
            strip.show();
            break;
          case 'f':
            //reset food LED
            LEDsaveState[1][0] = 255;
            LEDsaveState[1][1] = 255;
            strip.setPixelColor(0, strip.Color(LEDsaveState[1][0],LEDsaveState[1][1],LEDsaveState[1][2]));
            strip.show();
            break;
        }
        break;
    }
  }

  //take readings based on state
  if (state.compareTo("hall")){
    //read back button
    if (digitalRead(backButton) == "HIGH"){
      Serial.println("back");
    }
    else{
      //only do if still in this state
      //read hall
      int hallReading = analogRead(hallSensor);
      while (hallReading > hallMin && hallReading < hallMax){
        Serial.println("hall");
      }
    }  
  }
  else if (state.compareTo("force")){
    if (digitalRead(backButton) == "HIGH"){
      //send back message
      Serial.println("back");
    }
    else{
      //only do if still in this state
      //read force
      int forceReading = analogRead(forceSensor);
      while (forceReading > forceMin && forceReading < forceMax){
        Serial.println("force");
      }
    }
  }
  else if (state.compareTo("idle")){
    //read h/b buttons
    if(digitalRead(foodButton) == "HIGH"){
      Serial.println("food");
    }
    else if(digitalRead(playButton) == "HIGH"){
      Serial.println("play");
    }
  } 
  
}