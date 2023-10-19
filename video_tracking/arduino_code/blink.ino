#include <digitalWriteFast.h>

void setup() {
  Serial.begin(9600);
  pinMode(13, OUTPUT);
}

void loop() {
  // None
}

// Turn LED on for 1 ms when any character is received
void serialEvent() {    
    digitalWriteFast(13, HIGH);
    delay(2);
    digitalWriteFast(13, LOW);
    Serial.read();
}
