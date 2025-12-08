#include <Adafruit_NeoPixel.h>

#define NUM_LEDS 3
#define DATA_PIN 13

Adafruit_NeoPixel strip(NUM_LEDS, DATA_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();
  strip.show(); // initialize all LEDs to off
}

void loop() {
  strip.setPixelColor(0, strip.Color(255,0,0)); // first LED RED
  strip.setPixelColor(1, strip.Color(0,255,0)); // second LED GREEN
  strip.setPixelColor(2, strip.Color(0,0,255)); // third LED BLUE
  strip.show();

  while(true); // keep colors
}
