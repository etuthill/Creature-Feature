const int irPin = A0; // analog input pin for ir sensor
int lastValue = -1; // store last smoothed value
const int alpha = 4; // smoothing factor for exponential smoothing

void setup() {
  Serial.begin(9600); // start serial
  delay(1000); // short delay before starting
  Serial.println("ir sensor calibration started");
}

void loop() {
  // read sensor 3 times
  int x = analogRead(irPin);
  int y = analogRead(irPin);
  int z = analogRead(irPin);

  // take min of the three reads
  int irValue = min(min(x, y), z);

  if (lastValue == -1) {
    // first run, just set baseline
    lastValue = irValue;
  } else {
    // apply exponential smoothing
    irValue = (irValue + alpha * lastValue) / (alpha + 1);
  }

  lastValue = irValue; // update stored value
  Serial.println(irValue); // print smoothed result

}