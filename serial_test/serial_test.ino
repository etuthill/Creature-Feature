void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.flush();

}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() > 0) {
    // reads one char
    String command = String(Serial.read());
    String yeet = String("yeet");
    if (command.compareTo(yeet)) {
      Serial.println("yote");
    }
  } 

}