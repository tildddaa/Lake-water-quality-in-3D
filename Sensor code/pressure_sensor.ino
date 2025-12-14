const float OffSet = 0.491 ; // from calibration
float V, P;

// For filter
#define Pressure_samples 9
int pressureBuffer[Pressure_samples];
int pressureBufferTemp[Pressure_samples];
int getMedianNum(int arr[], int len);

void setup()
{
 Serial.begin(115200); // open serial port
 analogReadResolution(12);
 Serial.println("/** Water pressure sensor demo **/");
}

void loop()
{
  // Collect samples from A3
  for (int i = 0; i < Pressure_samples; i++) {
    pressureBuffer[i] = analogRead(3); 
    delay(5);                          // small delay between samples
  }

  // Copy buffer
  for (int i = 0; i < Pressure_samples; i++) {
    pressureBufferTemp[i] = pressureBuffer[i];
  }

  int medianADC = getMedianNum(pressureBufferTemp, Pressure_samples);
  
 
 V = analogRead(3) * 3.30 / 4096; //Sensor output voltage
 P = (V - OffSet) * 400; //Calculate water pressure
 Serial.print("Voltage:");
 Serial.print(V, 3);
 Serial.println("V");
 Serial.print(" Pressure:");
 Serial.print(P, 1);
 Serial.println(" KPa");
 Serial.println();

 delay(500);
}

// Median function (same as TDS sensor, so that we don't need two functions)
int getMedianNum(int bArray[], int len) {
  int bTab[len];
  for (int i = 0; i < len; i++) bTab[i] = bArray[i];

  for (int j = 0; j < len - 1; j++)
    for (int i = 0; i < len - j - 1; i++)
      if (bTab[i] > bTab[i + 1]) {
        int temp = bTab[i];
        bTab[i] = bTab[i + 1];
        bTab[i + 1] = temp;
      }

  if (len % 2 == 1)
    return bTab[len / 2];
  else
    return (bTab[len / 2] + bTab[len / 2 - 1]) / 2;
}


