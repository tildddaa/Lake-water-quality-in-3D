const float OffSet = 0.491 ;
float V, P;
void setup()
{
 Serial.begin(9600); // open serial port, set the baud rate to 9600 bps
 analogReadResolution(12);
 Serial.println("/** Water pressure sensor demo **/");
}
void loop()
{
 //Connect sensor to Analog 0
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
