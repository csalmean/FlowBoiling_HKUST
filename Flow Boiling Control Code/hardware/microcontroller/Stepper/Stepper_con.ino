// This MUST be flashed to the Ardunio before beginning experiments. This is the stepper driver, which tells the Arduino how to behave
// The arduino will read the serial connection, waiting for new commands to be sent.
// Command format: O45 (open 45 degrees), C20 (close 20 degrees) etc.

//defines pins
const int stepPin = 13;  //PUL -Pulse
const int dirPin = 12; //DIR -Direction
const int enPin = 11;  //ENA -Enable

char dir; // Holds direction of rotation (F, B)
float distance; // Holds rotational distance in degrees
int steps; // Holds number of steps needed to make this rotation
float steps_per_rot = 25600; // Holds number of steps in 360 degrees
int wait_for_transmission = 5; // Delay in ms in order to receive the serial data

void setup(){
  Serial.begin(9600);
  Serial.setTimeout(100);    // Instead of the default 1000ms, in order
                            // to speed up the Serial.parseInt() 
  
  //Sets the pins as Outputs
  pinMode(stepPin,OUTPUT); 
  pinMode(dirPin,OUTPUT);
  pinMode(enPin,OUTPUT);
  digitalWrite(enPin,HIGH);
}

void loop(){
    // Check if characters available in the buffer
    if (Serial.available() > 0) {
        dir = Serial.read();
        delay(wait_for_transmission); // If not delayed, second character is not correctly read
        distance = Serial.parseFloat(); // Waits for an int to be transmitted
        steps = steps_per_rot*distance/360;
        Serial.print(steps);
        Serial.print('\n');
        }
 
    switch (dir){
      case 'O': // Stepper forward, i.e. dirPin HIGH
        //Swtiches the motor on
        digitalWrite(enPin,LOW);
        //Sets motor direction as forward
        digitalWrite(dirPin,HIGH);
    
        //Makes the necessary number of pulses
        for(int x = 0; x < steps; x++){
            digitalWrite(stepPin,HIGH); 
            delayMicroseconds(1000); 
            digitalWrite(stepPin,LOW); 
            delayMicroseconds(1000); 
        }
        
        //Switches the motor off
        digitalWrite(enPin,HIGH);
        
        break;

      case 'C': // Stepper backward, i.e. dirPin LOW
        //Swtiches the motor on
        digitalWrite(enPin,LOW);
        //Sets motor direction as forward
        digitalWrite(dirPin,LOW);

        // LIMIT TO 45 DEGREES AT A TIME.
        
        //Makes 25600 Pulses for making one full cycle rotation
        for(int x = 0; x < steps; x++){
            digitalWrite(stepPin,HIGH); 
            delayMicroseconds(1000); 
            digitalWrite(stepPin,LOW); 
            delayMicroseconds(1000); 
          }
        
          digitalWrite(enPin, HIGH);
        
        break;
        
      default: // Unexpected char
        break;  
    }

    Serial.flush();
}
