#include <OneWire.h>

// Temp sensor
int DS18S20_Pin = 49; // DS18S20 Signal pin on digital 49
OneWire ds(DS18S20_Pin);

// TDS
#define TdsSensorPin A1
#define TDS_SCOUNT 30     // 30 samples for median filter
#define VREF 3.3
float kValue = 0.88;       // Calibration constant
float tdsValue = 0;
float averageVoltage = 0;
int tdsBuffer[TDS_SCOUNT];
int tdsBufferTemp[TDS_SCOUNT];
int tdsIndex = 0;

// Dissolved oxygen sensor
#define DO_PIN A2
#define ADC_RES 4096
#define DO_OFFSET 0.2325
uint16_t DO_Table[41] = {
    14460,14220,13820,13440,13090,12740,12420,12110,11810,11530,
    11260,11010,10770,10530,10300,10080,9860,9660,9460,9270,
    9080,8900,8730,8570,8410,8250,8110,7960,7820,7690,
    7560,7430,7300,7180,7070,6950,6840,6730,6630,6530,6410
};
#define CAL1_V 1600
#define CAL1_T 25

// pH sensor
#define PH_PIN A0
float phOffset = 0.12;

// Timers
unsigned long nowMillis = 0;
unsigned long lastTemp = 0;
unsigned long lastTDS = 0;
unsigned long lastPH = 0;
unsigned long lastDO = 0;

// Sampling intervals (start with 1 Hz, lower it if needed, now it reads the sensors every second)
const int TEMP_INTERVAL = 1000;
const int TDS_INTERVAL = 1000;
const int PH_INTERVAL = 1000;
const int DO_INTERVAL = 1000;

// Function declarations
float readTemperature();
void readPH(float tempC);
void readDOsensor(float tempC);
float computeDO(uint32_t mv, uint8_t tempC);
int getMedianNum(int bArray[], int len);

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  pinMode(PH_PIN, INPUT);     // Set sensor pins as input
  pinMode(TdsSensorPin, INPUT);
  pinMode(DO_PIN, INPUT);
}

void loop() {
  nowMillis = millis();

  // Temperature
  static float tempC = 25.0;
  if (nowMillis - lastTemp >= TEMP_INTERVAL) {
    lastTemp = nowMillis;
    float t = readTemperature();
    if (t > -100) tempC = t;  // ignore invalid readings

    Serial.print("Temperature (C): ");
    Serial.println(tempC);
  }

  // TDS
  if (nowMillis - lastTDS >= TDS_INTERVAL) {
    lastTDS = nowMillis;

    // Add ADC sample
    tdsBuffer[tdsIndex] = analogRead(TdsSensorPin);
    tdsIndex++;
    if (tdsIndex == TDS_SCOUNT) tdsIndex = 0;

    // Copy buffer for median filter
    for (int i = 0; i < TDS_SCOUNT; i++) {
      tdsBufferTemp[i] = tdsBuffer[i];
    }

    // Median filter to reduce noise
    averageVoltage = getMedianNum(tdsBufferTemp, TDS_SCOUNT) * VREF / 4096.0;

    // Temperature compensation
    float compensationCoefficient = 1.0 + 0.02 * (tempC - 25.0);
    float compensatedVoltage = averageVoltage / compensationCoefficient;

    // TDS calculation (convert from volts to ppm)
    tdsValue = (133.42 * compensatedVoltage * compensatedVoltage * compensatedVoltage
               - 255.86 * compensatedVoltage * compensatedVoltage
               + 857.39 * compensatedVoltage) * 0.5;

    Serial.print("TDS (ppm): ");
    Serial.println(tdsValue, 0);
  }
 

  // pH
  if (nowMillis - lastPH >= PH_INTERVAL) {
    lastPH = nowMillis;
    readPH(tempC);
  }

  // Dissolved oxygen
  if (nowMillis - lastDO >= DO_INTERVAL) {
    lastDO = nowMillis;
    readDOsensor(tempC);
  }
}

// Temperature function
float readTemperature() {
  byte data[12];
  byte addr[8];
  if (!ds.search(addr)) {
    ds.reset_search();
    return -1000;
  }

  if (OneWire::crc8(addr, 7) != addr[7]) {
    return -1000;
  }

  if (addr[0] != 0x10 && addr[0] != 0x28) {
    return -1000;
  }

  ds.reset();
  ds.select(addr);
  ds.write(0x44, 1); // start conversion

  ds.reset();
  ds.select(addr);
  ds.write(0xBE); // Read scratchpad

  for (int i = 0; i < 9; i++) data[i] = ds.read();

  ds.reset_search();

  byte MSB = data[1];
  byte LSB = data[0];
  float tempRead = ((MSB << 8) | LSB);
  float TemperatureSum = tempRead / 16.0;

  return TemperatureSum;
}

// TDS
// Median filter to reduce noise
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

// pH function
void readPH(float tempC) {
  int buf[10];

  for (int i = 0; i < 10; i++) {
    buf[i] = analogRead(PH_PIN);
    delay(10);
  }

  // sort 10 readings and uses median averageing to reduce noise
  for (int i = 0; i < 9; i++)
    for (int j = i + 1; j < 10; j++)
      if (buf[i] > buf[j]) {
        int t = buf[i];
        buf[i] = buf[j];
        buf[j] = t;
      }

  long avg = 0;
  for (int i = 2; i <= 7; i++) avg += buf[i];

  float voltage = avg * VREF / 4096.0 / 6.0;
  float pH_raw = 3.5 * voltage + phOffset;

  // Temperature compensation 0.03 pH/°C
  float pH_corrected = pH_raw + (tempC - 25.0) * 0.03;

  Serial.print("pH (temp compensated): ");
  Serial.println(pH_corrected, 2);
}

// Dissolved oxygen function
// Reads ADC, converts to millivolts, calculates DO using look-up table 
void readDOsensor(float tempC) {
    uint16_t raw = analogRead(DO_PIN);
    uint32_t mv = (uint32_t)VREF * raw / ADC_RES;

    float DO_corrected = computeDO(mv, (uint8_t)tempC);

    Serial.print("Dissolved Oxygen (corrected): ");
    Serial.print(DO_corrected, 3);
    Serial.println(" mg/L");
}

float computeDO(uint32_t mv, uint8_t tempC) {
    uint16_t V_sat = CAL1_V + 35 * tempC - CAL1_T * 35;
    uint32_t DO_raw_ugL = (mv * DO_Table[tempC] / V_sat);

    float DO_mgL = DO_raw_ugL / 1000.0;

    // add calibration offset
    float DO_corrected = DO_mgL + DO_OFFSET;

    return DO_corrected;
}

