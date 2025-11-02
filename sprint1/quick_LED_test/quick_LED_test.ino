const int redLED = 11;
const int greenLED = 10;
const int blueLED = 9;

void setup() {
  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(blueLED, OUTPUT);
}

void loop() {
  analogWrite(redLED, 100);
  analogWrite(greenLED, 0);
  analogWrite(blueLED, 0);
  delay(1000);
  analogWrite(redLED, 0);
  analogWrite(greenLED, 100);
  analogWrite(blueLED, 0);
  delay(1000);
}


