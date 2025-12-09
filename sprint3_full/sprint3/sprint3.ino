//dfhssfdfsdjhfsdhjewfuiwefuivdiufvuidfsu
#include <Servo.h>
#include <Adafruit_NeoPixel.h>

//led strip
#define NUM_LEDS 1
#define DATA_PIN 13
Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_GRB + NEO_KHZ800);

//map pins
const int hallSensor = A1;

//sensor vars
int hallMin = 0;
int hallMax = 999;

int LEDsaveState[3] = {0,255,0}; //food

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
}

void_loop(){
    if (Serial.available() > 0) {
    // reads one char
    String command = String(Serial.read());
    if command != None:
        //decrease food LED
        LEDsaveState[0] += 15;
        LEDsaveState[1] -= 15;
        strip.setPixelColor(0, strip.Color(LEDsaveState[0],LEDsaveState[1],LEDsaveState[2]));
        strip.show();   
    }
    
    //read hall
    int hallReading = analogRead(hallSensor);
    if hallReading > hallMin && hallReading < hallMax{
        Serial.println("hall");
        LEDsaveState[0] == 0;
        LEDsaveState[1] -= 255;
    }
    delay(50);
}