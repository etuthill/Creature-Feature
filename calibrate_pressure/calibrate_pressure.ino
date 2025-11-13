const int fsrPin = A0;  
int fsrReading;    

void setup() {
  Serial.begin(9600);
}

void loop() {
  fsrReading = analogRead(fsrPin); 
  Serial.println(fsrReading);   
  delay(100);                
}
