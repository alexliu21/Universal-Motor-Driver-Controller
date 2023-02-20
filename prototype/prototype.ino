#include <SPI.h>
#include <HighPowerStepperDriver.h>
#include <ArduinoSTL.h>
using namespace std;
HighPowerStepperDriver sd;
const uint16_t stepPeriodUs = 2000; //delay speed, increase to make motor slower, decrease to make motor faster (too fast, and it will skip steps)
const uint8_t CSPin = 4; //SCS pin

// variable declarations
String currentlimit;
String micro;
int micro2;
float curLim;
String steps;
float temp;
String pos;
int st;
int curLim2;
int whole;
int micr;

void setup()
{
  //An LED is Connected Pin12, doesn't work while using SPI because pin 12 is taken by MOSI
  
  //pinMode(LED_BUILTIN, OUTPUT);
  SPI.begin(); //initialize SPI
  sd.setChipSelectPin(CSPin); //assigned SCS pin

  // Give the driver some time to power up.
  delay(1);

  // Reset the driver to its default settings and clear latched status
  // conditions.
  sd.resetSettings();
  sd.clearStatus();

  // Select auto mixed decay.  TI's DRV8711 documentation recommends this mode
  // for most applications, and we find that it usually works well.
  sd.setDecayMode(HPSDDecayMode::AutoMixed);

  // Set the number of microsteps that correspond to one full step.
  sd.setStepMode(HPSDStepMode::MicroStep32);

  // Opens serial port, sets data rate to 9600 bps 8N1
  Serial.begin(9600);
}

void loop()
{
  char rxedByte = 0;

  if (Serial.available())
  {

    rxedByte = Serial.read();

    switch (rxedByte)
    {
      case 'Z': // current limit required first
      {
        currentlimit = Serial.readStringUntil('\n');
        //cout<<currentlimit;
        curLim = currentlimit.toFloat(); //convert string to float
        curLim2 = (int)curLim; //then to int

        sd.setCurrentMilliamps36v4(curLim2); //set current limit

        Serial.print("current limit set to: ");
        Serial.println(curLim2);
        Serial.println('\n');
        sd.enableDriver(); //enable the motor outputs

        break;
      }

      case 'M': // microstep mode
      {
        micro = Serial.readStringUntil('\n');
        temp = micro.toFloat();
        micro2 = (int)temp;
        sd.setStepMode(micro2);
        Serial.print("Microstepping mode set to: ");
        Serial.println(micro2);
        Serial.println('\n');
        
        break;
      }

      case 'F': // forward motor operation
      {
        Serial.print("Received: ");
        Serial.println(rxedByte);
        steps = Serial.readStringUntil('\n');
        temp = steps.toFloat();
        st = (int)floor(temp);
        Serial.println(st);
        sd.setDirection(0);
        for (unsigned int x = 0; x < st; x++)
        {
          sd.step();
          delayMicroseconds(stepPeriodUs);
        }

        delay(300); //delay not mandatory
        
        break;
      }

      case 'R': // reverse motor operation
      {
        Serial.print("Received: ");
        Serial.println(rxedByte);
        steps = Serial.readStringUntil('\n');
        temp = steps.toFloat();
        st = (int)floor(temp);
        Serial.println(st);
        sd.setDirection(1);
        for (unsigned int x = 0; x < st; x++)
        {
          sd.step();
          delayMicroseconds(stepPeriodUs);
        }
        
        delay(300); //delay not mandatory
        
        break;
      }

      case 'H': // go home reverse
      {
        pos = Serial.readStringUntil('\n');
        temp = pos.toFloat(); // string converted to float
        Serial.println(temp);
        whole = floor(temp);
        micr = (temp - whole) / 0.125;
        sd.setDirection(1);
        Serial.println(whole);
        Serial.println(micr);
        sd.setStepMode(1);
        for (unsigned int x = 0; x < whole; x++)
        {
          sd.step();
          delayMicroseconds(stepPeriodUs);
        }
        sd.setStepMode(8);
        for (unsigned int x = 0; x < micr; x++)
        {
          sd.step();
          delayMicroseconds(stepPeriodUs);
        }
        
        break;
      }

      case 'O': // go home forward
      {
        pos = Serial.readStringUntil('\n');
        temp = pos.toFloat(); // string converted to float
        Serial.println(temp);
        whole = floor(temp);
        micr = (temp - whole) / 0.125;
        sd.setDirection(0);
        Serial.println(whole);
        Serial.println(micr);
        sd.setStepMode(1);
        for (unsigned int x = 0; x < whole; x++)
        {
          sd.step();
          delayMicroseconds(stepPeriodUs);
        }
        sd.setStepMode(8);
        for (unsigned int x = 0; x < micr; x++)
        {
          sd.step();
          delayMicroseconds(stepPeriodUs);
        }
        
        break;
      }
       
      
      default:
        Serial.print("default: ");
        Serial.println(rxedByte);
        break;
    }//end of switch()
  }//endof if
}
