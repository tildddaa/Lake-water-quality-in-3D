# Bill of Materials

|Component|Use|Draw|
|-|-|-|
[Raft micro computer](https://docs.arduino.cc/hardware/due/)||
|[Arduino Due](https://www.amazon.se/Arduino-AG-utvecklingskort-Due-A000062/dp/B08933P95J?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=ANU9KP01APNAG)|Microcontroller for underwater|7V-12V|
[Raspberry Pi 5](https://se.farnell.com/raspberry-pi/rpi5-8gb-single/rpi-5-board-2-4ghz-8gb-arm-cortex/dp/4256000)|Onboard computer for sensor platform||
[Batteries 1.2V ](https://www.digikey.se/sv/products/detail/energizer-battery-company/NH15BP-8/4477694)|Batteries for powering the sensor system||
[Battery case](https://www.digikey.se/sv/products/detail/mpd-memory-protection-devices/BH28AAW/2439344)|||
[Battery charger](https://www.digikey.se/sv/products/detail/sparkfun-electronics/16718/16915572)|||
[Turbidity sensor](https://se.farnell.com/seeed-studio/101020752/turbidity-sensor-board-arduino/dp/4007740)|Measure water clarity||
[Temperature sensor](https://se.farnell.com/dfrobot/dfr0198/temp-sensor-probe-6mm-x-35mm-ss/dp/3517904)|Measure water temperature||
[Dissolved oxygen](https://se.farnell.com/dfrobot/sen0237-a/dev-kit-analog-dissolved-oxygen/dp/3517931)|Amount of oxygen available to life||
[PH sensor](https://se.farnell.com/dfrobot/sen0169/anal-ph-sensor-meter-pro-kit-arduino/dp/3517876)||5 V, 7 mA|
|[TDS (Total Dissolved Solids)](https://se.farnell.com/dfrobot/sen0244/analogue-tds-sensor-meter-kit/dp/3517934)|Measure water cleanness||
|[Hall effect sensor](https://www.electrokit.com/tlv49645-sip-3-hall-effektsensor-digital?gad_source=1&gad_campaignid=17338847491&gbraid=0AAAAAD_OrGN7ekLvdRKENoxCQ38xOgkfL&gclid=CjwKCAjwiY_GBhBEEiwAFaghvvtc5-3xuZx12bOuwTdUgIruGaBNhWvSB5BtiQO6VNAnJ_LaX2MxmBoCMSQQAvD_BwE) |Calculate depth of sensor platform||
|[Pressure sensor](https://www.digikey.com/en/products/detail/dfrobot/SEN0257/8341836) |Placed on the sensor platform to see where to measure and depth of measurment||
|Pulley|Lower sensor platform||
|[DC motor](https://www.biltema.se/bil---mc/lasta-och-dra/transporttillbehor/elektriska-vinschar/elvinsch-12-v-907-kg-2000042426?utm_source=google&utm_medium=cpc&utm_campaign=p-shopping-LIA-mid&gad_source=1&gad_campaignid=1603792037&gbraid=0AAAAADowiYi8V4ggsYYD4R_vxDRMR9FQR&gclid=Cj0KCQjwoP_FBhDFARIsANPG24PgOhgRuM1j2egWvMcDXaO6lrkzRsuYV2femD6pD6_SUT8Prufzs9IaAtKREALw_wcB)|Motor for pulley||
|[Water Proof Casing](https://bluerobotics.com/store/watertight-enclosures/wte-vp/)|Can handle up to 1000m depth||
|[Bulkhead Seal](https://bluerobotics.com/store/cables-connectors/penetrators/wlp-vp/)|To expose sensor to water, can handle 1000m depth||
|[SBC Buck converter: Diode](https://www.digikey.se/sv/products/detail/smc-diode-solutions/31DQ03/12142340)|Schottky diode||
|[SBC Buck converter: Inductor L1](https://www.digikey.se/sv/products/detail/pulse-electronics/PE-53115NL/2266016)|Designed for LM2574||
|[SBC Buck converter: Output capacitor C_out](https://www.digikey.se/sv/products/detail/panasonic-electronic-components/EEE-FT1V681UP/7560209)|Aluminium electrolyte capacitor||
|[SBC Buck converter: Input capacitor C_in](https://www.digikey.se/sv/products/detail/w%C3%BCrth-elektronik/865080343009/5728014)|Electrolytic capacitor||
|[SBC Buck converter: LM2574](https://www.digikey.se/sv/products/detail/texas-instruments/LM2574M-ADJ-NOPB/212609)|Switcher||
|[Stepper motor: 42BYGHM809](https://www.electrokit.com/stegmotor-0.90.41nm-bipolar?gad_source=1&gad_campaignid=17338847491&gbraid=0AAAAAD_OrGN0Xt-1ZuvYH1Pjt3kjsAX-x&gclid=Cj0KCQiAiKzIBhCOARIsAKpKLAMaXfz63mRY6ZiqTAR_Q3y5l7E4MAesszeU07BuEF7EYWXphvr5yMEaAvhrEALw_wcB)|Stepper motor||
|[Stepper motor driver: TB6600](https://opencircuit.se/product/tb6600-stepper-motor-driver)|Stepper motor driver||
|Turbidity Sensor|Components||
|Component|Use|Draw|
|-|-|-|
|Active Components|||
|[TLC271ACD](https://www.digikey.se/en/products/detail/texas-instruments/TLC271ACD/374879)|Op-Amp SOIC-8 for signal amplification|4x|
|[2N7002LT1G](https://www.digikey.se/en/products/detail/onsemi/2N7002/244345)|N-Channel MOSFET SOT-23 for LED switching|2x|
|Potentiometers|||
|[PVG5A104C03R00](https://www.digikey.se/en/products/detail/bourns-inc/PVG5A104C03R00/666289)|100kΩ Trimmer for gain calibration|2x|
|[PVG5A501C03R00](https://www.digikey.se/en/products/detail/bourns-inc/PVG5A501C03R00/666298)|500Ω Trimmer for LED current|2x|
|Resistors (0603)|||
|[RC0603FR-074K7L](https://www.digikey.se/en/products/detail/yageo/RC0603FR-074K7L/727212)|4.7kΩ Resistor|4x|
|[RC0603FR-071K2L](https://www.digikey.se/en/products/detail/yageo/RC0603FR-071K2L/726852)|1.2kΩ Resistor|4x|
|[RC0603FR-07100RL](https://www.digikey.se/en/products/detail/yageo/RC0603FR-07100RL/726888)|100Ω Resistor|2x|
|[RC0603FR-0720RL](https://www.digikey.se/en/products/detail/yageo/RC0603FR-0720RL/727039)|20Ω Resistor|2x|
|[RC0603FR-07270RL](https://www.digikey.se/en/products/detail/yageo/RC0603FR-07270RL/727103)|270Ω Resistor|2x|
|[RC0603FR-0713K7L](https://www.digikey.se/en/products/detail/yageo/RC0603FR-0713K7L/726933)|13.7kΩ Resistor|2x|
|Capacitors (0805)|||
|[CL21B223KBANNNC](https://www.digikey.se/en/products/detail/samsung-electro-mechanics/CL21B223KBANNNC/3886739)|22nF Capacitor X7R|2x|
|[CL21B105KAFNNNE](https://www.digikey.se/en/products/detail/samsung-electro-mechanics/CL21B105KAFNNNE/3886724)|1µF Capacitor X7R|2x|
|[C0805C339DCGACTU](https://se.farnell.com/kemet/c0805c339dcgactu/cap-3-3pf-500v-c0g-np0-0805/dp/2821038)|3.3pF Capacitor C0G|1x|
|[C0805C101J5GACTU](https://www.digikey.se/en/products/detail/kemet/C0805C101J5GACTU/411121)|100pF Capacitor C0G|1x|
|Diodes|||
|[BAT54,235](https://www.digikey.se/en/products/detail/diotec-semiconductor/BAT54/13163463)|Schottky Diode SOD-323|1x|
|LEDs - Indicator|||
|[APT1608SECK](https://www.digikey.se/en/products/detail/kingbright/APT1608SECK/1747518)|Orange Status LED 0603|1x|
|LEDs - Infrared|||
|[WP7113SF6C](https://www.digikey.se/en/products/detail/kingbright/WP7113SF6C/8591570)|860nm IR LED, 20° viewing angle|2x|
|[SFH 4855](https://www.digikey.se/en/products/detail/ams-osram-usa-inc/SFH-4855/5719277)|850nm IR LED, 16° viewing angle|1x|
|[LiteOn E2871](https://optoelectronics.liteon.com/upload/download/DS-50-92-0005/E2871.pdf)|940nm IR LED, 16° viewing angle|1x|
|[TSAL6100](https://www.digikey.se/en/products/detail/vishay-semiconductor-opto-division/TSAL6100/1681338)|940nm IR LED, 20° viewing angle|2x|
|Photodiodes|||
|[BPW 34 S-Z](https://www.digikey.se/en/products/detail/ams-osram-usa-inc/BPW-34-S-Z/1893856)|Photodiode 850nm peak, 80µA photocurrent|2x|

