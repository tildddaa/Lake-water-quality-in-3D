// --- Turbidity Sensor with Arduino Due ---
// Reads analog voltage from sensor and converts to NTU (Nephelometric Turbidity Units)

const int sensorPin = A0;   // Analog input pin
float voltage = 0.0;
float ntu = 0.0;

void setup() {
  Serial.begin(9600);
  analogReadResolution(12);   // Due has a 12-bit ADC (0–4095)
  analogReference(AR_DEFAULT); // Default reference is 3.3V
  delay(1000);
  Serial.println("Turbidity Sensor Reading Started...");
  Serial.println("--------------------------------");
}

void loop() {
  // --- Average multiple readings for stability ---
  long sum = 0;
  const int samples = 800;
  
  for (int i = 0; i < samples; i++) {
    sum += analogRead(sensorPin);
  }
  
  float raw = (float)sum / samples;
  
  // Convert ADC value to voltage (3.3V reference)
  voltage = (raw / 4095.0) * 3.3;
  
  // Optional calibration factor (adjust if sensor requires)
  voltage *= 1.4;   // You had this in original; keep if required after calibration

  // Round to 2 decimal places
  voltage = round_to_dp(voltage, 2);

  // --- Convert voltage to NTU (calibration equation) ---
  if (voltage < 2.5) {
    ntu = 3000;
  } else {
    ntu = -1120.4 * sq(voltage) + 5742.3 * voltage - 4353.8;
  }

  // --- Output to Serial Monitor ---
  Serial.print("Voltage: ");
  Serial.print(voltage, 2);
  Serial.print(" V | NTU: ");
  Serial.println(ntu, 2);

  delay(500); // small delay for readability
}

float round_to_dp(float in_value, int decimal_place) {
  float multiplier = pow(10.0f, decimal_place);
  in_value = roundf(in_value * multiplier) / multiplier;
  return in_value;
}