//dfhssfdfsdjhfsdhjewfuiwefuivdiufvuidfsu
#include <Servo.h>
#include <Adafruit_NeoPixel.h>

//led strip
#define NUM_LEDS 1
#define DATA_PIN 13
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_RGB + NEO_KHZ800);

//map pins
const int hallSensor = A1;

//sensor vars
int hallMin = 350;
int hallMax = 750;

// debounce hall effect
unsigned long lastEatTime = 0;
const unsigned long eatCooldown = 500;

// fluctuation buffer
int hallMinLo = hallMin - 30;
int hallMaxHi = hallMax + 30;

int LEDsaveState[3] = {0,255,0}; //food

bool wasEating = false;

void setup() {
  //Serial
  Serial.begin(9600);
  Serial.flush();

  //LED strip
  strip.begin();
  strip.setPixelColor(0, strip.Color(0,255,0)); // first LED GREEN
  strip.show();

  //initialize I/O pins
  pinMode(hallSensor, INPUT);
  delay(10000);
}

void loop(){
    //read serial
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');

        if (cmd.length() > 0) {
            char cmdType = cmd[0];
            char specific = cmd[3];
            if (cmdType == 'L'){
                LEDsaveState[0] += 15;
                LEDsaveState[1] -= 15;
                
                if (LEDsaveState[0] > 255) LEDsaveState[0] = 255;
                if (LEDsaveState[1] < 0) LEDsaveState[0] = 0;
                if (LEDsaveState[2] < 0) LEDsaveState[2] = 0;
                strip.setPixelColor(0, strip.Color(LEDsaveState[0], LEDsaveState[1], LEDsaveState[2]));
                strip.show();
            }
        }
    }

    //read hall
    int hallReading = analogRead(hallSensor);
    bool isEating = (hallReading < hallMinLo || hallReading > hallMaxHi);

    unsigned long now = millis();

    // enter eat
    if (isEating && !wasEating && (now - lastEatTime > eatCooldown)) {
        Serial.println("eat");
        lastEatTime = now;

        LEDsaveState[0] = 0;
        LEDsaveState[1] = 255;
        strip.setPixelColor(0, strip.Color(LEDsaveState[0], LEDsaveState[1], LEDsaveState[2]));
        strip.show();
    }

    // exit eat (ate)
    if (!isEating && wasEating) {
        Serial.println("ate"); // print once
    }

    wasEating = isEating;
    delay(50);
}