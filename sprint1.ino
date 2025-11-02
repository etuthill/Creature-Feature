#12-13
#include <Servo.h>
int pos = 0;
void setup() {
  // put your setup code here, to run once:
  myservo.attach(12);
  myservo.attach(13);
}

void loop() {
  // put your main code here, to run repeatedly:

}

for (pos = 500; pos <= 1000; pos +=1){
  myservo.writeMicroseconds(pos);
  delay(1)
}