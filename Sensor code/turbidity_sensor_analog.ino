// Grove Turbidity Sensor with Arduino
// Reads analog output and prints it on Serial Monitor

const int turbidityPin = A0;  // Connect SIG pin to A0 on Arduino
int turbidityValue = 0;       // To store ADC value
float voltage = 0;            // Converted voltage

void setup() {
  Serial.begin(9600);       // Start Serial Monitor
  pinMode(turbidityPin, INPUT);
}

void loop() {
  // Read analog value (0 - 1023 for 10-bit ADC)
  turbidityValue = analogRead(turbidityPin);

  // Convert ADC value to voltage (5V reference)
  voltage = turbidityValue * (5.0 / 1023.0);

  // Print readings
  Serial.print("Raw ADC Value: ");
  Serial.print(turbidityValue);
  Serial.print("  |  Voltage: ");
  Serial.print(voltage);
  Serial.println(" V");

  delay(500); // Wait half a second
}