// This MUST be flashed to the relevant Arduino before beginning the experiments.
// Arduino will then monitor the serial connection for new commands.
// If it receives 'a', then it switches on. If it receives 'b', it switches off.

const int period = 940;
int state= LOW;
int active = 0;

void setup() {
    pinMode(13, OUTPUT);
    active = 0;
  
    Serial.begin(9600); // Serial Port at 9600 baud
    Serial.setTimeout(50); // Instead of the default 1000ms, in order
                            // to speed up the Serial.parseInt() 
}

// the loop function runs over and over again forever
void loop() {
  // Check if characters available in the buffer
    if (Serial.available() > 0) {
        char inByte = Serial.read();

        switch(inByte){
          case 'a':
            active = 1;
            break;
          case 'b':
            active = 0;
            break;
        }
        Serial.print(active);
        }
    
    
    if (active == 1){
      // When switched on, the arduino will switch the state of the inverter (high or low), then wait for the prescribed duration.
      if (state == LOW){
        digitalWrite(13,HIGH);
        state=HIGH;
      }
      else if (state == HIGH){
        digitalWrite(13,LOW);
        state=LOW;
      }
    }

    delay(period);
    Serial.flush();
}
